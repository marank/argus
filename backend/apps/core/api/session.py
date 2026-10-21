"""Session based login for the single page app."""

import json

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.utils.translation import gettext as _
from ninja import Router, Schema, Status
from ninja.errors import HttpError
from ninja.utils import check_csrf

from apps.accounts.models import TwoFactor
from apps.accounts.schemas import CodeIn, CurrentUserOut, PreferencesIn, TwoFactorChallengeOut
from apps.accounts.services import throttle, two_factor
from apps.core.api.security import session_auth
from apps.core.notifications import EVENT_KEYS

# Plain session auth: the pickup terminal account must be able to sign in and out too.
router = Router(tags=["auth"], auth=session_auth)


class LoginIn(Schema):
    username: str
    password: str


def require_csrf(request: HttpRequest) -> None:
    if check_csrf(request) is not None:
        raise HttpError(403, _("CSRF verification failed. Please reload the page."))


@router.get("/csrf", auth=None, response={204: None})
def csrf(request: HttpRequest):
    """Sets the ``csrftoken`` cookie the frontend sends back as ``X-CSRFToken``."""
    get_token(request)
    return Status(204, None)


@router.post("/login", auth=None, response={200: CurrentUserOut, 202: TwoFactorChallengeOut})
def login_view(request: HttpRequest, payload: LoginIn):
    """Signs in, or (202) asks for the second step when the user switched it on."""
    require_csrf(request)
    request.session.pop(two_factor.PENDING_LOGIN, None)
    key = throttle.password_key(payload.username)
    if not throttle.attempt(key, throttle.PASSWORD_LIMIT):
        raise HttpError(429, _("Too many failed sign-ins. Please try again in 15 minutes."))
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None or not user.is_active:
        raise HttpError(401, _("Invalid username or password."))
    throttle.clear(key)
    second = TwoFactor.objects.filter(user=user).first()
    if second is not None:
        return Status(202, two_factor.start_login(request.session, user, second))
    login(request, user)
    return user


def pending_or_401(request: HttpRequest):
    pending = two_factor.pending_login(request.session)
    if pending is None:
        raise HttpError(401, _("The sign-in has expired. Please enter your password again."))
    return pending


@router.post("/login/verify", auth=None, response=CurrentUserOut)
def verify_login(request: HttpRequest, payload: CodeIn):
    """Second step: the app or email code, or a backup code."""
    require_csrf(request)
    state, user = pending_or_401(request)
    if not throttle.attempt(throttle.code_key(user), throttle.CODE_LIMIT):
        request.session.pop(two_factor.PENDING_LOGIN, None)
        raise HttpError(429, _("Too many wrong codes. Please try again in 15 minutes."))
    if not two_factor.check_login_code(user, state, payload.code):
        state["attempts"] += 1
        if state["attempts"] >= two_factor.MAX_ATTEMPTS:
            request.session.pop(two_factor.PENDING_LOGIN, None)
            raise HttpError(401, _("Too many wrong codes. Please enter your password again."))
        request.session[two_factor.PENDING_LOGIN] = state
        raise HttpError(400, _("The code is not correct or has expired."))
    request.session.pop(two_factor.PENDING_LOGIN, None)
    throttle.clear(throttle.code_key(user))
    login(request, user, backend=state["backend"])
    return user


@router.post("/login/resend", auth=None, response=TwoFactorChallengeOut)
def resend_login_code(request: HttpRequest):
    """Sends a new email code for the pending sign-in."""
    require_csrf(request)
    state, user = pending_or_401(request)
    if user.two_factor.method != TwoFactor.Method.EMAIL:
        raise HttpError(409, _("This sign-in uses an authenticator app."))
    if not two_factor.can_resend(state):
        raise HttpError(429, _("Please wait a moment before requesting another code."))
    sent = two_factor.issue_email_code(state, user)
    request.session[two_factor.PENDING_LOGIN] = state
    return {"two_factor": "email", "email_hint": two_factor.email_hint(user.email), "code_sent": sent}


@router.post("/logout", response={204: None})
def logout_view(request: HttpRequest):
    logout(request)
    return Status(204, None)


DASHBOARD_SIZES = {"small", "medium", "large"}
# "auto" fits the content (and the row); the others are fixed heights that scroll.
DASHBOARD_HEIGHTS = {"auto", "small", "medium", "large"}
# Room for a widget's own settings, such as the text of the notes widget.
WIDGET_OPTIONS_MAX = 10_000


def card_keys(value) -> list[str]:
    """Distinct card keys in their given order."""
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(c for c in value if isinstance(c, str) and 0 < len(c) <= 50))[:50]


def widget_options(value) -> dict:
    if not isinstance(value, dict) or len(json.dumps(value, ensure_ascii=False)) > WIDGET_OPTIONS_MAX:
        return {}
    return value


def clean_dashboard_settings(value: dict | None) -> dict:
    """Keeps only well-formed widget entries; the frontend owns the widget and card ids."""
    widgets, seen = [], set()
    for entry in (value or {}).get("widgets") or []:
        if not isinstance(entry, dict):
            continue
        widget_id = entry.get("id")
        if not isinstance(widget_id, str) or not widget_id or len(widget_id) > 50 or widget_id in seen:
            continue
        seen.add(widget_id)
        # Further instances of a widget name the widget they show.
        kind = entry.get("widget")
        widgets.append(
            {
                "id": widget_id,
                **({"widget": kind} if isinstance(kind, str) and 0 < len(kind) <= 50 else {}),
                "visible": bool(entry.get("visible", True)),
                "size": entry["size"] if entry.get("size") in DASHBOARD_SIZES else "large",
                "height": entry["height"] if entry.get("height") in DASHBOARD_HEIGHTS else "auto",
                "hidden_cards": card_keys(entry.get("hidden_cards")),
                # Cards in the user's order; empty keeps the default order.
                "card_order": card_keys(entry.get("card_order")),
                "options": widget_options(entry.get("options")),
            }
        )
    return {"widgets": widgets[:50]} if widgets else {}


@router.get("/me", response=CurrentUserOut)
def me(request: HttpRequest):
    return request.user


@router.patch("/me", response=CurrentUserOut)
def update_preferences(request: HttpRequest, payload: PreferencesIn):
    user = request.user
    for name, value in payload.dict(exclude_unset=True).items():
        if name == "notification_settings":
            value = {k: bool(v) for k, v in (value or {}).items() if k in EVENT_KEYS}
        elif name == "dashboard_settings":
            value = clean_dashboard_settings(value)
        setattr(user, name, value)
    user.save()
    return user

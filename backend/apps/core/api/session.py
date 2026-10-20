"""Session based login for the single page app."""

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.utils.translation import gettext as _
from ninja import Router, Schema, Status
from ninja.errors import HttpError
from ninja.utils import check_csrf

from apps.accounts.schemas import CurrentUserOut, PreferencesIn
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


@router.post("/login", auth=None, response=CurrentUserOut)
def login_view(request: HttpRequest, payload: LoginIn):
    require_csrf(request)
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None or not user.is_active:
        raise HttpError(401, _("Invalid username or password."))
    login(request, user)
    return user


@router.post("/logout", response={204: None})
def logout_view(request: HttpRequest):
    logout(request)
    return Status(204, None)


DASHBOARD_SIZES = {"small", "medium", "large"}


def card_keys(value) -> list[str]:
    """Distinct card keys in their given order."""
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(c for c in value if isinstance(c, str) and 0 < len(c) <= 50))[:50]


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
        widgets.append(
            {
                "id": widget_id,
                "visible": bool(entry.get("visible", True)),
                "size": entry["size"] if entry.get("size") in DASHBOARD_SIZES else "large",
                "hidden_cards": card_keys(entry.get("hidden_cards")),
                # Cards in the user's order; empty keeps the default order.
                "card_order": card_keys(entry.get("card_order")),
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

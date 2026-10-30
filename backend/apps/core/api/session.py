"""Session based login for the single page app."""

from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.middleware.csrf import get_token
from django.utils.translation import gettext as _
from ninja import Router, Status
from ninja.errors import HttpError
from ninja.utils import check_csrf

from apps.accounts.models import TwoFactor, TwoFactorMethod, User
from apps.accounts.schemas import CodeIn, CurrentUserOut, PreferencesIn, TwoFactorChallengeOut
from apps.accounts.services import dashboard_layout, throttle, two_factor
from apps.core.api.security import AuthedRequest, session_auth
from apps.core.notifications import receivable
from apps.core.schemas.base import Schema

# Plain session auth: the pickup terminal account must be able to sign in and out too.
router = Router(tags=["auth"], auth=session_auth)


class LoginIn(Schema):
    username: str
    password: str


def require_csrf(request: HttpRequest) -> None:
    if check_csrf(request) is not None:
        raise HttpError(403, _("CSRF verification failed. Please reload the page."))


@router.get("/csrf", auth=None, response={204: None})
def csrf(request: HttpRequest) -> Status[None]:
    """Sets the ``csrftoken`` cookie the frontend sends back as ``X-CSRFToken``."""
    get_token(request)
    return Status(204, None)


@router.post("/login", auth=None, response={200: CurrentUserOut, 202: TwoFactorChallengeOut})
def login_view(request: HttpRequest, payload: LoginIn) -> Status[two_factor.LoginChallenge] | User:
    """Signs in, or (202) asks for the second step when the user switched it on."""
    require_csrf(request)
    request.session.pop(two_factor.PENDING_LOGIN, None)
    key, address = throttle.password_key(payload.username), throttle.address_key(request)
    if not (
        throttle.attempt(address, throttle.ADDRESS_LIMIT) and throttle.attempt(key, throttle.PASSWORD_LIMIT)
    ):
        raise HttpError(429, _("Too many failed sign-ins. Please try again in 15 minutes."))
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None or not user.is_active:
        raise HttpError(401, _("Invalid username or password."))
    throttle.clear(key)
    throttle.refund(address)
    second = TwoFactor.objects.filter(user=user).first()
    if second is not None:
        return Status(202, two_factor.start_login(request.session, user, second))
    login(request, user)
    return user


def pending_or_401(request: HttpRequest) -> tuple[two_factor.LoginState, User]:
    pending = two_factor.pending_login(request.session)
    if pending is None:
        raise HttpError(401, _("The sign-in has expired. Please enter your password again."))
    return pending


@router.post("/login/verify", auth=None, response=CurrentUserOut)
def verify_login(request: HttpRequest, payload: CodeIn) -> User:
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
def resend_login_code(request: HttpRequest) -> two_factor.LoginChallenge:
    """Sends a new email code for the pending sign-in."""
    require_csrf(request)
    state, user = pending_or_401(request)
    if user.two_factor.method != TwoFactorMethod.EMAIL:
        raise HttpError(409, _("This sign-in uses an authenticator app."))
    if not two_factor.can_resend(state):
        raise HttpError(429, _("Please wait a moment before requesting another code."))
    sent = two_factor.issue_email_code(state, user)
    request.session[two_factor.PENDING_LOGIN] = state
    return {"two_factor": "email", "email_hint": two_factor.email_hint(user.email), "code_sent": sent}


@router.post("/logout", response={204: None})
def logout_view(request: AuthedRequest) -> Status[None]:
    logout(request)
    return Status(204, None)


@router.get("/me", response=CurrentUserOut)
def me(request: AuthedRequest) -> User:
    return request.user


@router.patch("/me", response=CurrentUserOut)
def update_preferences(request: AuthedRequest, payload: PreferencesIn) -> User:
    user = request.user
    for name, value in payload.dict(exclude_unset=True).items():
        if name in ("notification_settings", "app_notification_settings"):
            # Only what the user can get; nobody switches off what goes to others.
            allowed = receivable(user)
            value = {k: bool(v) for k, v in (value or {}).items() if k in allowed}
        elif name == "dashboard_settings":
            value = dashboard_layout.clean(value)
        setattr(user, name, value)
    user.save()
    return user

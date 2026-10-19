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


@router.get("/me", response=CurrentUserOut)
def me(request: HttpRequest):
    return request.user


@router.patch("/me", response=CurrentUserOut)
def update_preferences(request: HttpRequest, payload: PreferencesIn):
    user = request.user
    for name, value in payload.dict(exclude_unset=True).items():
        if name == "notification_settings":
            value = {k: bool(v) for k, v in (value or {}).items() if k in EVENT_KEYS}
        setattr(user, name, value)
    user.save()
    return user

"""How long a sign-in lasts: the site setting, or the user's own value."""

from django.contrib.auth import login
from django.http import HttpRequest

from apps.accounts.models import User
from apps.core.models import SiteSettings


def duration_seconds(user: User) -> int:
    hours = user.session_hours or SiteSettings.load().session_hours
    return hours * 3600


def sign_in(request: HttpRequest, user: User, backend: str | None = None) -> None:
    """Signs the user in for the configured duration (counted from the last change to the session)."""
    login(request, user, backend=backend)
    request.session.set_expiry(duration_seconds(user))

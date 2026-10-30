from typing import TYPE_CHECKING, Any

from django.http import HttpRequest
from django.utils.translation import gettext as _
from ninja.errors import HttpError
from ninja.security import SessionAuth

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from apps.accounts.models import User


class AuthedRequest(HttpRequest):
    """For type checking only: a request that passed the router's auth.

    Annotate ``request`` with it in endpoints that require a session, so
    ``request.user`` is the signed-in ``User`` instead of ``User | AnonymousUser``.
    Endpoints with ``auth=None`` keep ``HttpRequest``.
    """

    user: User


def is_it_staff(user: User | AnonymousUser | None) -> bool:
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def context_is_it_staff(context: dict[str, Any] | None) -> bool:
    """For schema resolvers: whether the response goes to IT staff (``context`` from ninja)."""
    request = (context or {}).get("request")
    return request is not None and is_it_staff(request.user)


class ITStaffAuth(SessionAuth):
    """Session auth that only admits members of the IT department.

    Authenticated users without IT permissions get a 403 instead of a 401 so the
    frontend can distinguish "not logged in" from "not allowed".
    """

    def authenticate(self, request: HttpRequest, key: str | None) -> User | None:
        user: User | None = super().authenticate(request, key)
        if user is None:
            return None
        if not is_it_staff(user):
            raise HttpError(403, _("This action is reserved for the IT department."))
        return user


class PermissionAuth(SessionAuth):
    """IT staff whose roles grant ``resource``: reading for GET, writing otherwise.

    With ``level`` the check is fixed, e.g. "write" for a router-wide action set
    or "read" for a lookup that is sent by POST.
    """

    def __init__(self, resource: str, level: str | None = None) -> None:
        super().__init__()
        self.resource = resource
        self.level = level

    def authenticate(self, request: HttpRequest, key: str | None) -> User | None:
        from apps.accounts.permissions import READ, WRITE, can

        user: User | None = super().authenticate(request, key)
        if user is None:
            return None
        if not is_it_staff(user):
            raise HttpError(403, _("This action is reserved for the IT department."))
        level = self.level or (READ if request.method in ("GET", "HEAD") else WRITE)
        if not can(user, self.resource, level):
            raise HttpError(403, _("Your roles do not allow this."))
        return user


def permission_auth(resource: str, level: str | None = None) -> PermissionAuth:
    return PermissionAuth(resource, level)


class EmployeeAuth(SessionAuth):
    """Default API auth: any employee, but not the shared pickup terminal account."""

    def authenticate(self, request: HttpRequest, key: str | None) -> User | None:
        user: User | None = super().authenticate(request, key)
        if user is not None and getattr(user, "is_terminal", False):
            raise HttpError(403, _("The pickup terminal can only access hand-outs."))
        return user


class TerminalAuth(SessionAuth):
    """The pickup terminal account, or IT staff (to test and support the terminal)."""

    def authenticate(self, request: HttpRequest, key: str | None) -> User | None:
        user: User | None = super().authenticate(request, key)
        if user is None:
            return None
        if not (getattr(user, "is_terminal", False) or is_it_staff(user)):
            raise HttpError(403, _("This page is reserved for the pickup terminal."))
        return user


class SuperuserAuth(SessionAuth):
    """Administrators only (system settings such as the LDAP login)."""

    def authenticate(self, request: HttpRequest, key: str | None) -> User | None:
        user: User | None = super().authenticate(request, key)
        if user is None:
            return None
        if not user.is_superuser:
            raise HttpError(403, _("This action is reserved for administrators."))
        return user


session_auth = SessionAuth()
employee_auth = EmployeeAuth()
it_staff_auth = ITStaffAuth()
terminal_auth = TerminalAuth()
superuser_auth = SuperuserAuth()

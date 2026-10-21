import logging
from typing import Annotated
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import FilterLookup, FilterSchema
from ninja.errors import HttpError

from apps.accounts.models import User
from apps.accounts.permissions import WRITE, can
from apps.accounts.schemas import UserIn, UserOut
from apps.accounts.services import two_factor
from apps.core.api.crud import CrudConfig, build_crud_router
from apps.core.api.security import permission_auth

logger = logging.getLogger(__name__)


class UserFilter(FilterSchema):
    department: Annotated[UUID | None, FilterLookup("department_id")] = None
    is_active: bool | None = None
    is_staff: bool | None = None


def protect_administrators(request: HttpRequest, user: User) -> None:
    if user.is_superuser and not request.user.is_superuser:
        raise HttpError(403, _("Only administrators can change or delete an administrator."))
    if request.method == "DELETE" and user.pk == request.user.pk:
        raise HttpError(409, _("You cannot delete your own account."))


def changes_members(data: dict, user: User | None, relation: str) -> bool:
    """Whether the input sets other teams or roles than the user has (None = unchanged)."""
    wanted = data.get(relation)
    if wanted is None:
        return False
    current = set(getattr(user, relation).values_list("pk", flat=True)) if user else set()
    return set(wanted) != current


def check_user_input(request: HttpRequest, data: dict, user: User | None) -> None:
    """Rights beyond editing users, and no lockout.

    Only administrators appoint administrators and hand out roles (otherwise anyone
    editing users could raise their own rights); teams need the right to edit teams.
    Only an active administrator changes administrators, so with these rules one
    always stays: the one making the change.
    """
    if changes_members(data, user, "roles") and not request.user.is_superuser:
        raise HttpError(403, _("Only administrators can assign roles."))
    if changes_members(data, user, "teams") and not can(request.user, "teams", WRITE):
        raise HttpError(403, _("You may not change teams."))

    own = user is not None and user.pk == request.user.pk
    if own and user.is_active and data.get("is_active") is False:
        raise HttpError(409, _("You cannot deactivate your own account."))

    wanted = data.get("is_superuser")
    if wanted is not None and wanted != (user.is_superuser if user else False):
        if not request.user.is_superuser:
            raise HttpError(403, _("Only administrators can appoint administrators."))
        if own:
            raise HttpError(409, _("You cannot remove your own administrator rights."))


def new_user() -> User:
    # Accounts created here sign in via LDAP or get a password with `manage.py set_password`;
    # until then no password matches (an empty one would fail validation).
    user = User()
    user.set_unusable_password()
    return user


def prepare_user(data: dict) -> dict:
    # Fields left out (None) stay as they are.
    for name in ("is_superuser", "teams", "roles"):
        if data.get(name) is None:
            data.pop(name, None)
    # The location only applies to terminal accounts.
    if not data.get("is_terminal"):
        data["terminal_location"] = None
    return data


router = build_crud_router(
    CrudConfig(
        model=User,
        out_schema=UserOut,
        in_schema=UserIn,
        filter_schema=UserFilter,
        permission="users",
        check_change=protect_administrators,
        check_input=check_user_input,
        new=new_user,
        prepare=prepare_user,
        search_fields=("username", "first_name", "last_name", "email", "employee_number"),
        ordering_fields=(
            "username",
            "last_name",
            "first_name",
            "email",
            "employee_number",
            "department__sort_order",
            "department__name",
        ),
        queryset=lambda: User.objects.select_related(
            "department", "terminal_location__parent", "two_factor"
        ).prefetch_related("roles", "teams"),
    ),
    tags=["users"],
)


@router.post("/{uuid:pk}/two-factor/reset", response=UserOut, auth=permission_auth("users", WRITE))
def reset_two_factor(request: HttpRequest, pk: UUID):
    """For users who lost their phone and backup codes: they sign in with the password alone again."""
    user = get_object_or_404(User.objects.select_related("department", "terminal_location__parent"), pk=pk)
    if user.pk == request.user.pk:
        raise HttpError(409, _("Disable your own two-factor authentication in your profile."))
    if user.is_superuser and not request.user.is_superuser:
        raise HttpError(403, _("Only administrators can reset the sign-in of an administrator."))
    two_factor.disable(user)
    logger.info("%s reset the two-factor sign-in of %s", request.user, user)
    return user

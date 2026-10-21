import logging
from typing import Annotated
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import FilterLookup, FilterSchema
from ninja.errors import HttpError

from apps.accounts.models import User
from apps.accounts.permissions import WRITE
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


router = build_crud_router(
    CrudConfig(
        model=User,
        out_schema=UserOut,
        in_schema=UserIn,
        filter_schema=UserFilter,
        permission="users",
        check_change=protect_administrators,
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
        ).prefetch_related("roles"),
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

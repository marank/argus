from typing import Annotated
from uuid import UUID

from ninja import FilterLookup, FilterSchema

from apps.accounts.models import User
from apps.accounts.schemas import UserIn, UserOut
from apps.core.api.crud import CrudConfig, build_crud_router


class UserFilter(FilterSchema):
    department: Annotated[UUID | None, FilterLookup("department_id")] = None
    is_active: bool | None = None
    is_staff: bool | None = None


router = build_crud_router(
    CrudConfig(
        model=User,
        out_schema=UserOut,
        in_schema=UserIn,
        filter_schema=UserFilter,
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
        queryset=lambda: User.objects.select_related("department", "terminal_location__parent"),
    ),
    tags=["users"],
)

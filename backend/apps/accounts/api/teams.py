from typing import Annotated
from uuid import UUID

from ninja import FilterLookup, FilterSchema

from apps.accounts.models import Team
from apps.accounts.schemas import TeamIn, TeamOut
from apps.core.api.crud import CrudConfig, build_crud_router


class TeamFilter(FilterSchema):
    ids: Annotated[list[UUID] | None, FilterLookup("id__in")] = None
    member: Annotated[UUID | None, FilterLookup("members")] = None


# Teams are IT-internal; the whole router is IT-only (see config/api.py).
router = build_crud_router(
    CrudConfig(
        model=Team,
        out_schema=TeamOut,
        in_schema=TeamIn,
        filter_schema=TeamFilter,
        search_fields=("name", "code"),
        ordering_fields=("name", "code", "sort_order"),
        queryset=lambda: Team.objects.prefetch_related("members"),
    ),
    tags=["teams"],
)

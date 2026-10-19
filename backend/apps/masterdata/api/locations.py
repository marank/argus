from typing import Annotated
from uuid import UUID

from ninja import FilterLookup, FilterSchema

from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import Location
from apps.masterdata.schemas.location import LocationIn, LocationOut


class LocationFilter(FilterSchema):
    parent: Annotated[UUID | None, FilterLookup("parent_id")] = None
    kind: str | None = None
    is_pickup_point: bool | None = None


router = build_crud_router(
    CrudConfig(
        model=Location,
        out_schema=LocationOut,
        in_schema=LocationIn,
        filter_schema=LocationFilter,
        search_fields=("name", "code", "parent__name"),
        ordering_fields=("name", "code", "kind"),
        queryset=lambda: Location.objects.select_related("parent__parent"),
    ),
    tags=["locations"],
)

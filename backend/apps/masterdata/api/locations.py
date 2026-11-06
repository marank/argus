from typing import Annotated
from uuid import UUID

from django.db.models import F, QuerySet
from django.db.models.functions import Coalesce
from ninja import FilterLookup, FilterSchema

from apps.accounts.permissions import ResourceKey
from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import Location
from apps.masterdata.schemas.location import LocationIn, LocationOut


def location_queryset() -> QuerySet[Location]:
    # `site`: name of the top-level location (up to four levels), used to group the list.
    return Location.objects.select_related("parent__parent").annotate(
        site=Coalesce(
            F("parent__parent__parent__name"), F("parent__parent__name"), F("parent__name"), F("name")
        )
    )


class LocationFilter(FilterSchema):
    parent: Annotated[UUID | None, FilterLookup("parent_id")] = None
    kind: Annotated[list[str] | None, FilterLookup("kind__in")] = None
    is_pickup_point: bool | None = None


router = build_crud_router(
    CrudConfig(
        model=Location,
        out_schema=LocationOut,
        in_schema=LocationIn,
        filter_schema=LocationFilter,
        permission=ResourceKey.LOCATIONS,
        search_fields=("name", "code", "parent__name"),
        ordering_fields=("name", "code", "kind", "site"),
        queryset=location_queryset,
    ),
    tags=["locations"],
)

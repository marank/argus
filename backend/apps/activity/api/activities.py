from datetime import date
from typing import Annotated
from uuid import UUID

from django.db.models import QuerySet
from ninja import FilterLookup, FilterSchema, Query, Router
from ninja.pagination import paginate

from apps.activity.models import Activity
from apps.activity.schemas import ActivityOut
from apps.activity.services.log import visible
from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import AuthedRequest, it_staff_auth

# Each row is filtered by the right to read its area.
router = Router(tags=["activity"], auth=it_staff_auth)


class ActivityFilter(FilterSchema):
    area: Annotated[list[str] | None, FilterLookup("area__in")] = None
    kind: Annotated[list[str] | None, FilterLookup("kind__in")] = None
    actor: Annotated[list[UUID] | None, FilterLookup("actor_id__in")] = None
    since: Annotated[date | None, FilterLookup("occurred_at__date__gte")] = None
    until: Annotated[date | None, FilterLookup("occurred_at__date__lte")] = None


ACTIVITY_ORDERING_FIELDS = (
    "occurred_at",
    "area",
    "kind",
    "subject_label",
    "actor__last_name",
    "actor_id",
    "related_user__last_name",
)


@router.get("", response=list[ActivityOut])
@paginate(Pagination)
def list_activities(
    request: AuthedRequest,
    filters: Query[ActivityFilter],
    q: str | None = None,
    ordering: str | None = None,
) -> QuerySet[Activity]:
    """Everything IT did, newest first: requests, devices, stock, licenses, reports, orders."""
    queryset = filters.filter(visible(request.user))
    queryset = search(
        queryset,
        q,
        ("subject_label", "detail", "actor__last_name", "actor__first_name", "related_user__last_name"),
    )
    return order(queryset, ordering, ACTIVITY_ORDERING_FIELDS)

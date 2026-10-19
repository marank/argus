from typing import Annotated
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import FilterLookup, FilterSchema, Query, Router
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import it_staff_auth
from apps.inventory.models import AssetIssue
from apps.inventory.schemas.asset_issue import AssetIssueOut, AssetIssueUpdateIn
from apps.inventory.services.issues import update_issue

router = Router(tags=["issues"], auth=it_staff_auth)


class IssueFilter(FilterSchema):
    status: Annotated[list[str] | None, FilterLookup("status__in")] = None
    asset: Annotated[UUID | None, FilterLookup("asset_id")] = None
    kind: str | None = None


def issue_queryset():
    return AssetIssue.objects.select_related(
        "asset__model__manufacturer", "asset__assigned_to", "reported_by", "handled_by"
    )


@router.get("", response=list[AssetIssueOut])
@paginate(Pagination)
def list_issues(
    request: HttpRequest,
    filters: Query[IssueFilter],
    q: str | None = None,
    ordering: str | None = None,
):
    queryset = search(
        filters.filter(issue_queryset()),
        q,
        (
            "description",
            "asset__inventory_number",
            "asset__model__name",
            "reported_by__first_name",
            "reported_by__last_name",
        ),
    )
    return order(queryset, ordering, ("created_at", "status", "kind", "asset__inventory_number"))


@router.put("/{uuid:pk}", response=AssetIssueOut)
def update(request: HttpRequest, pk: UUID, payload: AssetIssueUpdateIn):
    """Take a report into work or resolve it with a note for the employee."""
    issue = get_object_or_404(AssetIssue, pk=pk)
    update_issue(issue, request.user, payload.status, payload.resolution)
    return issue_queryset().get(pk=pk)

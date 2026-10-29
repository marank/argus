from typing import Annotated
from uuid import UUID

from django.db.models import Prefetch, QuerySet
from django.shortcuts import get_object_or_404
from ninja import FilterLookup, FilterSchema, Query, Router
from ninja.pagination import paginate

from apps.accounts.services import assignment
from apps.accounts.services.assignment import Assigned, assigned_q
from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import AuthedRequest, permission_auth
from apps.inventory.models import AssetIssue, AssetIssueEntry
from apps.inventory.schemas.asset_issue import (
    AssetIssueDetailOut,
    AssetIssueOut,
    AssetIssueUpdateIn,
    AssignIn,
    IssueMessageIn,
)
from apps.inventory.services import notifications
from apps.inventory.services.issues import post_message, update_issue

router = Router(tags=["issues"], auth=permission_auth("issues"))


class IssueFilter(FilterSchema):
    status: Annotated[list[str] | None, FilterLookup("status__in")] = None
    asset: Annotated[UUID | None, FilterLookup("asset_id")] = None
    kind: str | None = None
    team: Annotated[list[UUID] | None, FilterLookup("assigned_team_id__in")] = None
    assignee: Annotated[UUID | None, FilterLookup("assignee_id")] = None


def issue_queryset():
    return AssetIssue.objects.select_related(
        "asset__model__manufacturer",
        "asset__assigned_to",
        "reported_by",
        "handled_by",
        "assigned_team",
        "assignee",
    )


@router.get("", response=list[AssetIssueOut])
@paginate(Pagination)
def list_issues(
    request: AuthedRequest,
    filters: Query[IssueFilter],
    q: str | None = None,
    ordering: str | None = None,
    assigned: Assigned | None = None,
):
    """``assigned`` works as for requests: ``me``, ``my_teams`` or ``nobody``."""
    queryset = search(
        filters.filter(issue_queryset()).filter(assigned_q(request.user, assigned)),
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


def issue_detail(issues: QuerySet[AssetIssue], pk: UUID) -> AssetIssue:
    """A report with its conversation and the other reports on its device among ``issues``.

    IT passes all reports, the reporter only their own.
    """
    issue = get_object_or_404(
        issues.select_related(
            "asset__model__manufacturer",
            "asset__model__category",
            "asset__assigned_to",
            "asset__location__parent",
            "reported_by__department",
            "handled_by",
            "assigned_team",
            "assignee",
        ).prefetch_related(Prefetch("entries", queryset=AssetIssueEntry.objects.select_related("author"))),
        pk=pk,
    )
    for entry in issue.entries.all():
        entry.side = "reporter" if entry.author_id and entry.author_id == issue.reported_by_id else "it"
    issue.other_issues = list(issues.filter(asset=issue.asset_id).exclude(pk=issue.pk))
    issue.still_assigned = bool(issue.reported_by_id) and issue.asset.assigned_to_id == issue.reported_by_id
    return issue


@router.get("/{uuid:pk}", response=AssetIssueDetailOut)
def detail(request: AuthedRequest, pk: UUID):
    return issue_detail(AssetIssue.objects.all(), pk)


@router.put("/{uuid:pk}", response=AssetIssueDetailOut)
def update(request: AuthedRequest, pk: UUID, payload: AssetIssueUpdateIn):
    """Change the status (into work, resolved, reopened), optionally with a message."""
    issue = get_object_or_404(AssetIssue, pk=pk)
    update_issue(issue, request.user, payload.status, payload.message, by_it=True)
    return issue_detail(AssetIssue.objects.all(), pk)


@router.post("/{uuid:pk}/messages", response=AssetIssueDetailOut)
def message(request: AuthedRequest, pk: UUID, payload: IssueMessageIn):
    post_message(get_object_or_404(AssetIssue, pk=pk), request.user, payload.text, by_it=True)
    return issue_detail(AssetIssue.objects.all(), pk)


@router.post("/{uuid:pk}/assign", response=AssetIssueDetailOut)
def assign(request: AuthedRequest, pk: UUID, payload: AssignIn):
    issue = get_object_or_404(AssetIssue, pk=pk)
    if assignment.assign(issue, payload.team, payload.assignee, request.user):
        notifications.issue_assigned(issue)
    return issue_detail(AssetIssue.objects.all(), pk)

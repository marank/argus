"""The approvals page of department approvers: requests waiting for their decision."""

from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404
from ninja import Router
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import search
from apps.core.api.security import AuthedRequest
from apps.requests.models import AssetRequest, AssetRequestStatus
from apps.requests.schemas.asset_request import (
    ApproveIn,
    AssetRequestListOut,
    AssetRequestOut,
    DeclineIn,
)
from apps.requests.services import workflow

from .queries import approvable_asset_requests, get_asset_request, get_for_update

router = Router(tags=["approvals"])


@router.get("", response=list[AssetRequestListOut])
@paginate(Pagination)
def list_approvals(request: AuthedRequest, q: str | None = None) -> QuerySet[AssetRequest]:
    """Requests waiting for a decision, the oldest first; once decided they leave the list."""
    queryset = (
        approvable_asset_requests(request.user)
        .filter(status=AssetRequestStatus.PENDING_APPROVAL)
        .order_by("created_at")
    )
    return search(
        queryset,
        q,
        ("number", "title", "requester__first_name", "requester__last_name", "requester__username"),
    )


def _decidable(request: AuthedRequest, pk: UUID) -> AssetRequest:
    """A locked request the user approves for; others are not found.

    Checked before any status check, so nobody learns the state of a request
    outside their departments.
    """
    if not approvable_asset_requests(request.user).filter(pk=pk).exists():
        raise Http404
    return get_for_update(pk)


@router.post("/{uuid:pk}/approve", response=AssetRequestOut)
@transaction.atomic
def approve(request: AuthedRequest, pk: UUID, payload: ApproveIn) -> AssetRequest:
    workflow.approve(_decidable(request, pk), request.user, payload.comment)
    return get_asset_request(request, pk, as_approver=True)


@router.post("/{uuid:pk}/decline", response=AssetRequestOut)
@transaction.atomic
def decline(request: AuthedRequest, pk: UUID, payload: DeclineIn) -> AssetRequest:
    workflow.decline(_decidable(request, pk), request.user, payload.comment)
    return get_asset_request(request, pk, as_approver=True)

"""The approvals page of department approvers: requests waiting for their decision."""

from uuid import UUID

from django.http import HttpRequest
from ninja import Router
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import search
from apps.reservations.models import Reservation
from apps.reservations.schemas.reservation import (
    ApproveIn,
    DeclineIn,
    ReservationListOut,
    ReservationOut,
)
from apps.reservations.services import workflow

from .queries import approvable_reservations, get_for_update, get_reservation

router = Router(tags=["approvals"])


@router.get("", response=list[ReservationListOut])
@paginate(Pagination)
def list_approvals(request: HttpRequest, pending: bool = True, q: str | None = None):
    """Waiting requests, the oldest first; with ``pending=false`` the decided ones, newest first."""
    queryset = approvable_reservations(request.user)
    if pending:
        queryset = queryset.filter(status=Reservation.Status.PENDING_APPROVAL).order_by("created_at")
    else:
        queryset = queryset.exclude(status=Reservation.Status.PENDING_APPROVAL).order_by("-created_at")
    return search(
        queryset,
        q,
        ("number", "title", "requester__first_name", "requester__last_name", "requester__username"),
    )


@router.post("/{uuid:pk}/approve", response=ReservationOut)
def approve(request: HttpRequest, pk: UUID, payload: ApproveIn):
    workflow.approve(get_for_update(pk), request.user, payload.comment)
    return get_reservation(request, pk, as_approver=True)


@router.post("/{uuid:pk}/decline", response=ReservationOut)
def decline(request: HttpRequest, pk: UUID, payload: DeclineIn):
    workflow.decline(get_for_update(pk), request.user, payload.comment)
    return get_reservation(request, pk, as_approver=True)

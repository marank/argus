from datetime import date
from typing import Annotated
from uuid import UUID

from django.db.models import Q
from django.http import HttpRequest
from django.utils import timezone
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.accounts.models import User
from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import is_it_staff, it_staff_auth
from apps.reservations.models import Reservation
from apps.reservations.schemas.reservation import (
    ApproveIn,
    HandOutIn,
    ReadyIn,
    RejectIn,
    ReservationIn,
    ReservationListOut,
    ReservationOut,
    ScheduleIn,
)
from apps.reservations.services import workflow

from .queries import get_for_update, get_reservation, visible_reservations

router = Router(tags=["reservations"])


class ReservationFilter(FilterSchema):
    status: Annotated[list[str] | None, FilterLookup("status__in")] = None
    requester: Annotated[UUID | None, FilterLookup("requester_id")] = None
    department: Annotated[UUID | None, FilterLookup("requester__department_id")] = None
    duration: str | None = None
    start_from: Annotated[date | None, FilterLookup("start_date__gte")] = None
    start_until: Annotated[date | None, FilterLookup("start_date__lte")] = None
    overdue: bool | None = None
    open: bool | None = None

    def filter_overdue(self, value: bool | None) -> Q:
        if not value:
            return Q()
        return Q(status=Reservation.Status.HANDED_OUT, end_date__lt=timezone.localdate())

    def filter_open(self, value: bool | None) -> Q:
        return Q(status__in=Reservation.OPEN_STATUSES) if value else Q()


@router.get("", response=list[ReservationListOut])
@paginate(Pagination)
def list_reservations(
    request: HttpRequest,
    filters: Query[ReservationFilter],
    q: str | None = None,
    ordering: str | None = None,
    mine: bool = False,
):
    """IT staff see every reservation, employees only their own."""
    queryset = filters.filter(visible_reservations(request))
    if mine:
        queryset = queryset.filter(requester=request.user)
    queryset = search(
        queryset,
        q,
        ("number", "title", "requester__first_name", "requester__last_name", "requester__username"),
    )
    return order(
        queryset,
        ordering,
        ("number", "created_at", "start_date", "end_date", "pickup_at", "status"),
    )


@router.post("", response={201: ReservationOut})
def create_reservation(request: HttpRequest, payload: ReservationIn):
    data = payload.dict(exclude={"items", "requester"})
    requester = request.user
    if payload.requester and is_it_staff(request.user):
        requester = User.objects.get(pk=payload.requester)
    items = [item.dict() for item in payload.items]
    reservation = workflow.submit(requester, data, items, created_by=request.user)
    return Status(201, get_reservation(request, reservation.pk))


@router.get("/{uuid:pk}", response=ReservationOut)
def get_reservation_detail(request: HttpRequest, pk: UUID):
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/cancel", response=ReservationOut)
def cancel(request: HttpRequest, pk: UUID):
    reservation = get_reservation(request, pk)
    workflow.cancel(reservation, request.user)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/approve", response=ReservationOut, auth=it_staff_auth)
def approve(request: HttpRequest, pk: UUID, payload: ApproveIn):
    quantities = {item.id: item.quantity_approved for item in payload.items}
    workflow.approve(
        get_for_update(pk),
        request.user,
        quantities,
        payload.pickup_at,
        payload.pickup_location,
        payload.comment,
    )
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/reject", response=ReservationOut, auth=it_staff_auth)
def reject(request: HttpRequest, pk: UUID, payload: RejectIn):
    workflow.reject(get_for_update(pk), request.user, payload.comment)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/schedule", response=ReservationOut, auth=it_staff_auth)
def schedule(request: HttpRequest, pk: UUID, payload: ScheduleIn):
    workflow.reschedule(
        get_for_update(pk), request.user, payload.pickup_at, payload.pickup_location, payload.handover_mode
    )
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/ready", response=ReservationOut, auth=it_staff_auth)
def mark_ready(request: HttpRequest, pk: UUID, payload: ReadyIn):
    workflow.mark_ready(get_for_update(pk), request.user, payload.handover_mode)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/hand-out", response=ReservationOut, auth=it_staff_auth)
def hand_out(request: HttpRequest, pk: UUID, payload: HandOutIn):
    """Hand out without the pickup terminal; documented by the IT staff member."""
    workflow.hand_out(
        get_for_update(pk),
        request.user,
        method=payload.method,
        received_by_id=payload.received_by,
        received_by_name=payload.received_by_name,
        notes=payload.notes,
        location=payload.location,
        allocation_notes={n.allocation: n.note for n in payload.allocation_notes},
    )
    return get_reservation(request, pk)

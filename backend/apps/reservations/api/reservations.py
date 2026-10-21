from datetime import date
from typing import Annotated
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.accounts.models import User
from apps.accounts.permissions import WRITE, can
from apps.accounts.services import assignment
from apps.accounts.services.assignment import Assigned, assigned_q
from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import permission_auth
from apps.reservations.models import Reservation
from apps.reservations.schemas.reservation import (
    AssignIn,
    ConfirmIn,
    DirectRequestIn,
    ExtendIn,
    HandOutIn,
    ReadyIn,
    RejectIn,
    ReservationIn,
    ReservationListOut,
    ReservationOut,
    ScheduleIn,
)
from apps.reservations.services import history, workflow
from apps.reservations.services import notifications as reservation_notifications

from .queries import get_for_update, get_reservation, visible_reservations

router = Router(tags=["reservations"])
# IT's decisions on requests; employees only list, create and cancel their own.
reservations_write = permission_auth("reservations", WRITE)


class ReservationFilter(FilterSchema):
    status: Annotated[list[str] | None, FilterLookup("status__in")] = None
    requester: Annotated[UUID | None, FilterLookup("requester_id")] = None
    department: Annotated[UUID | None, FilterLookup("requester__department_id")] = None
    duration: str | None = None
    start_from: Annotated[date | None, FilterLookup("start_date__gte")] = None
    start_until: Annotated[date | None, FilterLookup("start_date__lte")] = None
    overdue: bool | None = None
    open: bool | None = None
    team: Annotated[list[UUID] | None, FilterLookup("assigned_team_id__in")] = None
    assignee: Annotated[UUID | None, FilterLookup("assignee_id")] = None
    origin: str | None = None

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
    assigned: Assigned | None = None,
):
    """IT staff with the right to see requests see all of them, everyone else their own.

    ``assigned``: ``me`` – assigned to the current user; ``my_teams`` – to one of
    their teams or to them; ``nobody`` – neither a team nor a person set.
    """
    queryset = filters.filter(visible_reservations(request))
    if mine:
        queryset = queryset.filter(requester=request.user)
    queryset = queryset.filter(assigned_q(request.user, assigned))
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
    data = payload.dict(exclude={"items", "requester", "follows"})
    requester = request.user
    if payload.requester and can(request.user, "reservations", WRITE):
        requester = User.objects.get(pk=payload.requester)
    if payload.follows:
        # Only an earlier request of the same employee that the user may see.
        data["follows"] = (
            visible_reservations(request).filter(pk=payload.follows, requester=requester).first()
        )
    items = [item.dict() for item in payload.items]
    reservation = workflow.submit(requester, data, items, created_by=request.user)
    return Status(201, get_reservation(request, reservation.pk))


@router.post("/direct", response={201: ReservationOut}, auth=reservations_write)
def create_direct(request: HttpRequest, payload: DirectRequestIn):
    """A request with specific devices from stock: confirmed and allocated right away."""
    requester = (
        get_object_or_404(User, pk=payload.requester, is_active=True) if payload.requester else request.user
    )
    reservation = workflow.prepare_direct(
        requester,
        request.user,
        payload.dict(exclude={"requester", "assets", "consumables"}),
        assets=payload.assets,
        consumables={c.consumable: c.quantity for c in payload.consumables},
    )
    return Status(201, get_reservation(request, reservation.pk))


@router.get("/{uuid:pk}", response=ReservationOut)
def get_reservation_detail(request: HttpRequest, pk: UUID):
    return get_reservation(request, pk, as_approver=True)


@router.post("/{uuid:pk}/cancel", response=ReservationOut)
def cancel(request: HttpRequest, pk: UUID):
    reservation = get_reservation(request, pk)
    workflow.cancel(reservation, request.user)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/confirm", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def confirm(request: HttpRequest, pk: UUID, payload: ConfirmIn):
    quantities = {item.id: item.quantity_confirmed for item in payload.items}
    workflow.confirm(
        get_for_update(pk),
        request.user,
        quantities,
        payload.pickup_at,
        payload.pickup_location,
        payload.comment,
    )
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/reject", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def reject(request: HttpRequest, pk: UUID, payload: RejectIn):
    workflow.reject(get_for_update(pk), request.user, payload.comment)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/schedule", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def schedule(request: HttpRequest, pk: UUID, payload: ScheduleIn):
    workflow.reschedule(
        get_for_update(pk), request.user, payload.pickup_at, payload.pickup_location, payload.handover_mode
    )
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/ready", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def mark_ready(request: HttpRequest, pk: UUID, payload: ReadyIn):
    reservation = get_for_update(pk)
    if {"pickup_at", "pickup_location"} & payload.model_fields_set:
        workflow.reschedule(
            reservation,
            request.user,
            payload.pickup_at if "pickup_at" in payload.model_fields_set else reservation.pickup_at,
            payload.pickup_location
            if "pickup_location" in payload.model_fields_set
            else reservation.pickup_location_id,
        )
    workflow.mark_ready(reservation, request.user, payload.handover_mode, payload.skip_device_check)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/reopen", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def reopen(request: HttpRequest, pk: UUID):
    """Take a ready request back into preparation."""
    workflow.reopen(get_for_update(pk), request.user)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/extend", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def extend(request: HttpRequest, pk: UUID, payload: ExtendIn):
    """Move the return date of a handed-out request."""
    workflow.extend(get_for_update(pk), request.user, payload.end_date)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/remind", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def remind(request: HttpRequest, pk: UUID):
    """Email the employee to return the devices."""
    workflow.remind(get_for_update(pk), request.user)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/assign", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def assign(request: HttpRequest, pk: UUID, payload: AssignIn):
    reservation = get_for_update(pk)
    before = (reservation.assigned_team_id, reservation.assignee_id)
    notify = assignment.assign(reservation, payload.team, payload.assignee, request.user)
    if (reservation.assigned_team_id, reservation.assignee_id) != before:
        history.record(
            reservation,
            history.Kind.ASSIGNED,
            request.user,
            team=reservation.assigned_team.name if reservation.assigned_team else None,
            assignee=reservation.assignee.display_name if reservation.assignee else None,
        )
    if notify:
        reservation_notifications.request_assigned(reservation)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/hand-out", response=ReservationOut, auth=reservations_write)
@transaction.atomic
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

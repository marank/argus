from datetime import date
from typing import Annotated
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.accounts.models import User
from apps.accounts.permissions import WRITE, can
from apps.accounts.services.assignment import Assigned, assigned_q
from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import permission_auth
from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset
from apps.reservations.models import Reservation
from apps.reservations.schemas.reservation import (
    AssignIn,
    ConfirmIn,
    DirectRequestIn,
    ExtendIn,
    HandOutIn,
    QuickAssignIn,
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
# IT's decisions on requests; employees only list, create and cancel their own.
reservations_write = permission_auth("reservations", WRITE)


def _employee(pk: UUID) -> User:
    """Whom IT records something for: a current employee, not a deactivated account or a terminal."""
    employee = User.objects.filter(pk=pk, is_active=True, is_terminal=False).first()
    if employee is None:
        raise BusinessError(_("Choose an active employee."))
    return employee


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
    may_record = can(request.user, "reservations", WRITE)
    if payload.requester and may_record:
        requester = _employee(payload.requester)
    if payload.follows:
        # Only an earlier request of the same employee that the user may see.
        data["follows"] = (
            visible_reservations(request).filter(pk=payload.follows, requester=requester).first()
        )
    items = [item.dict() for item in payload.items]
    reservation = workflow.submit(
        requester, data, items, created_by=request.user, from_catalog=not may_record
    )
    return Status(201, get_reservation(request, reservation.pk))


@router.post("/direct", response={201: ReservationOut}, auth=reservations_write)
def create_direct(request: HttpRequest, payload: DirectRequestIn):
    """A request with specific devices from stock: confirmed and allocated right away."""
    requester = _employee(payload.requester) if payload.requester else request.user
    reservation = workflow.prepare_direct(
        requester,
        request.user,
        payload.dict(exclude={"requester", "assets", "consumables"}),
        assets=payload.assets,
        consumables={c.consumable: c.quantity for c in payload.consumables},
    )
    return Status(201, get_reservation(request, reservation.pk))


@router.post("/quick", response={201: ReservationOut}, auth=reservations_write)
def quick_assign(request: HttpRequest, payload: QuickAssignIn):
    """A device from stock assigned to an employee in one step: recorded as handed out."""
    requester = _employee(payload.requester)
    reservation = workflow.quick_assign(
        get_object_or_404(Asset, pk=payload.asset),
        requester,
        request.user,
        duration=payload.duration,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    return Status(201, get_reservation(request, reservation.pk))


@router.get("/{uuid:pk}", response=ReservationOut)
def get_reservation_detail(request: HttpRequest, pk: UUID):
    return get_reservation(request, pk, as_approver=True)


@router.post("/{uuid:pk}/cancel", response=ReservationOut)
@transaction.atomic
def cancel(request: HttpRequest, pk: UUID):
    get_reservation(request, pk)  # only a request the user may see
    workflow.cancel(get_for_update(pk), request.user)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/confirm", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def confirm(request: HttpRequest, pk: UUID, payload: ConfirmIn):
    quantities = {item.id: item.quantity_confirmed for item in payload.items}
    workflow.confirm(get_for_update(pk), request.user, quantities, payload.comment)
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
        get_for_update(pk),
        request.user,
        payload.pickup_at,
        payload.pickup_location,
        payload.handover_mode,
        notify=payload.notify,
    )
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/ready", response=ReservationOut, auth=reservations_write)
@transaction.atomic
def mark_ready(request: HttpRequest, pk: UUID, payload: ReadyIn):
    given = payload.model_fields_set
    workflow.mark_ready(
        get_for_update(pk),
        request.user,
        payload.handover_mode,
        payload.skip_device_check,
        pickup_at=payload.pickup_at if "pickup_at" in given else workflow.KEEP,
        pickup_location_id=payload.pickup_location if "pickup_location" in given else workflow.KEEP,
        notify=payload.notify,
    )
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
    workflow.assign(get_for_update(pk), payload.team, payload.assignee, request.user)
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

"""Shared pickup terminal: employees review prepared devices and sign for them."""

from uuid import UUID

from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.accounts.models import User
from apps.core.api.security import terminal_auth
from apps.reservations.models import Reservation
from apps.reservations.schemas.reservation import ReservationOut
from apps.reservations.schemas.terminal import TerminalPersonOut, TerminalPickupOut, TerminalSignIn
from apps.reservations.services import workflow

from .queries import get_for_update, reservation_queryset

router = Router(tags=["pickup terminal"], auth=terminal_auth)


def pickups():
    return reservation_queryset().filter(
        status=Reservation.Status.READY, handover_mode=Reservation.HandoverMode.PICKUP
    )


@router.get("/pickups", response=list[TerminalPickupOut])
def list_pickups(request: HttpRequest, q: str | None = None):
    """Prepared pickups, next pickup first."""
    queryset = pickups()
    if q:
        queryset = queryset.filter(
            Q(number__icontains=q)
            | Q(requester__first_name__icontains=q)
            | Q(requester__last_name__icontains=q)
            | Q(requester__username__icontains=q)
        )
    return list(queryset.order_by("pickup_at", "start_date"))


@router.get("/pickups/{uuid:pk}", response=ReservationOut)
def get_pickup(request: HttpRequest, pk: UUID):
    return get_object_or_404(pickups(), pk=pk)


@router.post("/pickups/{uuid:pk}/sign", response=ReservationOut)
def sign(request: HttpRequest, pk: UUID, payload: TerminalSignIn):
    """Complete the hand-out with the collecting person's signature."""
    reservation = get_object_or_404(
        Reservation, pk=pk, status=Reservation.Status.READY, handover_mode=Reservation.HandoverMode.PICKUP
    )
    workflow.hand_out(
        get_for_update(reservation.pk),
        request.user,
        method="signature",
        received_by_id=payload.received_by,
        received_by_name=payload.received_by_name,
        signature=payload.signature,
        notes=payload.notes,
        allocation_notes={n.allocation: n.note for n in payload.allocation_notes},
    )
    return get_object_or_404(reservation_queryset(), pk=pk)


@router.get("/people", response=list[TerminalPersonOut])
def people(request: HttpRequest, q: str = ""):
    """Minimal employee lookup to record who collects the devices."""
    if len(q.strip()) < 2:
        return []
    return list(
        User.objects.filter(is_active=True, is_terminal=False)
        .filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q))
        .select_related("department")[:15]
    )

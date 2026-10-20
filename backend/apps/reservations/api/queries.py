from uuid import UUID

from django.db.models import Prefetch, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import can
from apps.reservations.models import (
    DeviceReturn,
    Reservation,
    ReservationAllocation,
    ReservationEvent,
    ReservationItem,
)


def reservation_queryset() -> QuerySet[Reservation]:
    allocations = ReservationAllocation.objects.select_related(
        "asset__model__manufacturer",
        "consumable__model__manufacturer",
        "consumable__location__parent",
        "license__model__manufacturer",
        "license__model__category",
        "license_assignment__asset__model__manufacturer",
        "allocated_by",
    )
    items = (
        ReservationItem.objects.select_related(
            "category", "asset_model__manufacturer", "asset_model__category"
        )
        .annotate(_quantity_allocated=Coalesce(Sum("allocations__quantity"), 0))
        # Aggregating queries ignore Meta.ordering, so keep the requested order explicitly.
        .order_by("position")
        .prefetch_related(Prefetch("allocations", queryset=allocations))
    )
    return Reservation.objects.select_related(
        "requester__department",
        "created_by",
        "handled_by",
        "prepared_by",
        "assigned_team",
        "assignee",
        "approver",
        "pickup_location__parent",
        "follows",
        "handover__received_by",
        "handover__handed_out_by",
        "handover__recorded_by",
    ).prefetch_related(
        Prefetch("items", queryset=items),
        Prefetch("returns", queryset=DeviceReturn.objects.select_related("returned_by")),
        Prefetch("events", queryset=ReservationEvent.objects.select_related("actor")),
    )


def visible_reservations(request: HttpRequest) -> QuerySet[Reservation]:
    queryset = reservation_queryset()
    if can(request.user, "reservations"):
        return queryset
    return queryset.filter(requester=request.user)


def approvable_reservations(user) -> QuerySet[Reservation]:
    """Requests that went to one of the departments ``user`` approves for."""
    return (
        reservation_queryset()
        .filter(requester__department__approvers=user)
        .exclude(approval=Reservation.Approval.NOT_REQUIRED)
    )


def get_reservation(request: HttpRequest, pk: UUID, *, as_approver: bool = False) -> Reservation:
    """A request the user may see; ``as_approver`` adds those they decide on."""
    reservation = visible_reservations(request).filter(pk=pk).first()
    if reservation is None and as_approver:
        reservation = approvable_reservations(request.user).filter(pk=pk).first()
    if reservation is None:
        raise Http404
    return reservation


def get_for_update(pk: UUID) -> Reservation:
    """Plain instance for workflow transitions (no prefetch caches that could go stale)."""
    return get_object_or_404(Reservation, pk=pk)

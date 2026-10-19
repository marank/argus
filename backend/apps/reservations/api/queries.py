from uuid import UUID

from django.db.models import Prefetch, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from apps.core.api.security import is_it_staff
from apps.reservations.models import DeviceReturn, Reservation, ReservationAllocation, ReservationItem


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
        "pickup_location__parent",
        "handover__received_by",
        "handover__handed_out_by",
        "handover__recorded_by",
    ).prefetch_related(
        Prefetch("items", queryset=items),
        Prefetch("returns", queryset=DeviceReturn.objects.select_related("returned_by")),
    )


def visible_reservations(request: HttpRequest) -> QuerySet[Reservation]:
    queryset = reservation_queryset()
    if is_it_staff(request.user):
        return queryset
    return queryset.filter(requester=request.user)


def get_reservation(request: HttpRequest, pk: UUID) -> Reservation:
    return get_object_or_404(visible_reservations(request), pk=pk)


def get_for_update(pk: UUID) -> Reservation:
    """Plain instance for workflow transitions (no prefetch caches that could go stale)."""
    return get_object_or_404(Reservation, pk=pk)

from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import Router, Schema

from apps.core.api.security import permission_auth
from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, Consumable, License
from apps.inventory.services.availability import pool_assets, pool_consumables, pool_licenses
from apps.masterdata.models import AssetModel
from apps.reservations.models import ReservationAllocation, ReservationItem
from apps.reservations.schemas.reservation import (
    AllocateIn,
    CandidatesOut,
    ReservationOut,
    ResolveItemIn,
    ReturnIn,
)
from apps.reservations.services import workflow

from .queries import get_for_update, get_reservation

router = Router(tags=["reservation preparation"], auth=permission_auth("reservations"))


class AutoAllocateOut(Schema):
    allocated: int
    reservation: ReservationOut


@router.get("/items/{uuid:item_id}/candidates", response=CandidatesOut)
def candidates(request: HttpRequest, item_id: UUID, q: str | None = None):
    """Devices from the pool (or free license seats) that could be allocated to an item."""
    item = get_object_or_404(ReservationItem.objects.select_related("reservation"), pk=item_id)
    if item.is_free_text:
        return {"assets": [], "consumables": []}
    filters = {"model_id": item.asset_model_id, "category_id": item.category_id}
    if item.is_software:
        devices = Asset.objects.filter(assigned_to=item.reservation.requester_id).select_related(
            "model__manufacturer"
        )
        return {
            "assets": [],
            "consumables": [],
            "licenses": list(pool_licenses(**filters)),
            "devices": list(devices.order_by("inventory_number")),
        }
    assets = pool_assets(**filters).select_related("model__manufacturer", "location__parent")
    if q:
        assets = assets.filter(Q(inventory_number__icontains=q) | Q(serial_number__icontains=q))
    consumables = [
        s
        for s in pool_consumables(**filters).select_related("model__manufacturer", "location__parent")
        if s.available_quantity > 0
    ]
    return {"assets": list(assets.order_by("inventory_number")[:100]), "consumables": consumables}


@router.post("/{uuid:pk}/allocations", response=ReservationOut)
def allocate(request: HttpRequest, pk: UUID, payload: AllocateIn):
    """Bind a device to the reservation, by id or by scanning its code."""
    item = get_object_or_404(ReservationItem, pk=payload.item, reservation_id=pk)
    if payload.code:
        asset = Asset.objects.filter(
            Q(inventory_number__iexact=payload.code) | Q(serial_number__iexact=payload.code)
        ).first()
        if asset is None:
            raise BusinessError(_("No device found for “%(code)s”.") % {"code": payload.code})
        workflow.allocate_asset(item, asset, request.user)
    elif payload.license:
        license = get_object_or_404(License, pk=payload.license)
        device = get_object_or_404(Asset, pk=payload.asset) if payload.asset else None
        workflow.allocate_license(item, license, request.user, device)
    elif payload.asset:
        workflow.allocate_asset(item, get_object_or_404(Asset, pk=payload.asset), request.user)
    elif payload.consumable:
        consumable = get_object_or_404(Consumable, pk=payload.consumable)
        workflow.allocate_consumable(item, consumable, payload.quantity, request.user)
    else:
        raise BusinessError(_("Choose a device or consumable."))
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/items/{uuid:item_id}/resolve", response=ReservationOut)
def resolve_item(request: HttpRequest, pk: UUID, item_id: UUID, payload: ResolveItemIn):
    """Assign a catalog model to a free-text line (e.g. one IT just created)."""
    item = get_object_or_404(ReservationItem, pk=item_id, reservation_id=pk)
    workflow.resolve_item(item, get_object_or_404(AssetModel, pk=payload.asset_model), request.user)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/auto-allocate", response=AutoAllocateOut)
@transaction.atomic
def auto_allocate(request: HttpRequest, pk: UUID):
    allocated = workflow.auto_allocate(get_for_update(pk), request.user)
    return {"allocated": allocated, "reservation": get_reservation(request, pk)}


@router.delete("/{uuid:pk}/allocations/{uuid:allocation_id}", response=ReservationOut)
def remove_allocation(request: HttpRequest, pk: UUID, allocation_id: UUID):
    allocation = get_object_or_404(
        ReservationAllocation.objects.select_related("item__reservation", "asset", "consumable"),
        pk=allocation_id,
        item__reservation_id=pk,
    )
    workflow.remove_allocation(allocation, request.user)
    return get_reservation(request, pk)


@router.post("/{uuid:pk}/return", response=ReservationOut)
@transaction.atomic
def return_devices(request: HttpRequest, pk: UUID, payload: ReturnIn):
    workflow.return_devices(
        get_for_update(pk),
        request.user,
        payload.allocations,
        notes=payload.notes,
        allocation_notes={n.allocation: n.note for n in payload.allocation_notes},
        damaged=set(payload.damaged),
    )
    return get_reservation(request, pk)

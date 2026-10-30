from typing import NotRequired, TypedDict
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import Router, Schema

from apps.core.api.security import AuthedRequest, permission_auth
from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, Consumable, License
from apps.inventory.services.availability import pool_assets, pool_consumables, pool_licenses
from apps.masterdata.models import AssetModel
from apps.requests.models import AssetRequest, AssetRequestAllocation, AssetRequestItem
from apps.requests.schemas.asset_request import (
    AllocateIn,
    AssetRequestOut,
    CandidatesOut,
    ResolveItemIn,
    ReturnIn,
)
from apps.requests.services import workflow

from .queries import get_asset_request, get_for_update

router = Router(tags=["request preparation"], auth=permission_auth("requests"))


class AutoAllocateOut(Schema):
    allocated: int
    asset_request: AssetRequestOut


class AutoAllocated(TypedDict):
    """What ``auto_allocate`` returns, serialized as ``AutoAllocateOut``."""

    allocated: int
    asset_request: AssetRequest


class Candidates(TypedDict):
    """What ``candidates`` returns, serialized as ``CandidatesOut``."""

    assets: list[Asset]
    consumables: list[Consumable]
    licenses: NotRequired[list[License]]
    devices: NotRequired[list[Asset]]


@router.get("/items/{uuid:item_id}/candidates", response=CandidatesOut)
def candidates(request: AuthedRequest, item_id: UUID, q: str | None = None) -> Candidates:
    """Devices from the pool (or free license seats) that could be allocated to an item."""
    item = get_object_or_404(AssetRequestItem.objects.select_related("asset_request"), pk=item_id)
    if item.is_free_text:
        return {"assets": [], "consumables": []}
    filters = {"model_id": item.asset_model_id, "category_id": item.category_id}
    if item.is_software:
        devices = Asset.objects.filter(assigned_to=item.asset_request.requester_id).select_related(
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


def _asset_by_code(code: str) -> Asset:
    """The device with this inventory number, else the one with this serial number.

    Inventory numbers are unique; serial numbers of different manufacturers may
    collide, and then guessing would hand out the wrong device.
    """
    asset = Asset.objects.filter(inventory_number__iexact=code).first()
    if asset:
        return asset
    matches = list(Asset.objects.filter(serial_number__iexact=code)[:2])
    if not matches:
        raise BusinessError(_("No device found for “%(code)s”.") % {"code": code})
    if len(matches) > 1:
        raise BusinessError(
            _("Several devices have the serial number “%(code)s”. Scan the inventory number instead.")
            % {"code": code}
        )
    return matches[0]


@router.post("/{uuid:pk}/allocations", response=AssetRequestOut)
def allocate(request: AuthedRequest, pk: UUID, payload: AllocateIn) -> AssetRequest:
    """Bind a device to the request, by id or by scanning its code."""
    item = get_object_or_404(AssetRequestItem, pk=payload.item, asset_request_id=pk)
    if payload.code:
        workflow.allocate_asset(item, _asset_by_code(payload.code), request.user)
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
    return get_asset_request(request, pk)


@router.post("/{uuid:pk}/items/{uuid:item_id}/resolve", response=AssetRequestOut)
def resolve_item(request: AuthedRequest, pk: UUID, item_id: UUID, payload: ResolveItemIn) -> AssetRequest:
    """Assign a catalog model to a free-text line (e.g. one IT just created)."""
    item = get_object_or_404(AssetRequestItem, pk=item_id, asset_request_id=pk)
    workflow.resolve_item(item, get_object_or_404(AssetModel, pk=payload.asset_model), request.user)
    return get_asset_request(request, pk)


@router.post("/{uuid:pk}/auto-allocate", response=AutoAllocateOut)
@transaction.atomic
def auto_allocate(request: AuthedRequest, pk: UUID, item: UUID | None = None) -> AutoAllocated:
    """Fill the open items from the pool; with `item` only that one."""
    allocated = workflow.auto_allocate(get_for_update(pk), request.user, item)
    return {"allocated": allocated, "asset_request": get_asset_request(request, pk)}


@router.delete("/{uuid:pk}/allocations/{uuid:allocation_id}", response=AssetRequestOut)
@transaction.atomic
def remove_allocation(request: AuthedRequest, pk: UUID, allocation_id: UUID) -> AssetRequest:
    get_for_update(pk)  # waits for other changes to the request
    allocation = get_object_or_404(
        AssetRequestAllocation.objects.select_related("item__asset_request", "asset", "consumable"),
        pk=allocation_id,
        item__asset_request_id=pk,
    )
    workflow.remove_allocation(allocation, request.user)
    return get_asset_request(request, pk)


@router.post("/{uuid:pk}/return", response=AssetRequestOut)
@transaction.atomic
def return_devices(request: AuthedRequest, pk: UUID, payload: ReturnIn) -> AssetRequest:
    workflow.return_devices(
        get_for_update(pk),
        request.user,
        payload.allocations,
        notes=payload.notes,
        allocation_notes={n.allocation: n.note for n in payload.allocation_notes},
        damaged=set(payload.damaged),
    )
    return get_asset_request(request, pk)

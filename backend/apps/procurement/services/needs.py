"""What still has to be ordered: open request demand and consumables below minimum."""

from typing import TypedDict
from uuid import UUID

from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from apps.inventory.models import Consumable
from apps.inventory.services.availability import available_count
from apps.procurement.models import PurchaseOrder, PurchaseOrderLine
from apps.requests.models import AssetRequest, AssetRequestItem, AssetRequestStatus


def _on_order_by_item() -> dict[UUID, int]:
    rows = (
        PurchaseOrderLine.objects.filter(
            asset_request_item__isnull=False, order__status__in=PurchaseOrder.OPEN_STATUSES
        )
        .values("asset_request_item")
        .annotate(open=Coalesce(Sum(F("quantity") - F("quantity_received")), 0))
    )
    return {row["asset_request_item"]: row["open"] for row in rows}


def _on_order_by_model() -> dict[UUID, int]:
    rows = (
        PurchaseOrderLine.objects.filter(
            asset_model__isnull=False,
            asset_request_item__isnull=True,
            order__status__in=PurchaseOrder.OPEN_STATUSES,
        )
        .values("asset_model")
        .annotate(open=Coalesce(Sum(F("quantity") - F("quantity_received")), 0))
    )
    return {row["asset_model"]: row["open"] for row in rows}


class AssetRequestNeed(TypedDict):
    asset_request_item: AssetRequestItem
    asset_request: AssetRequest
    missing: int
    available: int
    on_order: int
    to_order: int


class ConsumableNeed(TypedDict):
    consumable: Consumable
    missing: int
    on_order: int
    to_order: int


class Needs(TypedDict):
    requests: list[AssetRequestNeed]
    consumables: list[ConsumableNeed]


def asset_request_needs() -> list[AssetRequestNeed]:
    on_order = _on_order_by_item()
    items = AssetRequestItem.objects.filter(
        asset_request__status__in=(AssetRequestStatus.SUBMITTED, AssetRequestStatus.CONFIRMED)
    ).select_related(
        "asset_request__requester",
        "asset_model__manufacturer",
        "asset_model__default_supplier",
        "category",
    )
    needs: list[AssetRequestNeed] = []
    for item in items:
        missing = item.quantity_missing
        if not missing:
            continue
        # Free-text lines match nothing in the pool until IT assigns a model.
        available = (
            0
            if item.is_free_text
            else available_count(category_id=item.category_id, model_id=item.asset_model_id)
        )
        ordered = on_order.get(item.pk, 0)
        shortfall = max(missing - available - ordered, 0)
        needs.append(
            {
                "asset_request_item": item,
                "asset_request": item.asset_request,
                "missing": missing,
                "available": available,
                "on_order": ordered,
                "to_order": shortfall,
            }
        )
    return needs


def consumable_needs() -> list[ConsumableNeed]:
    on_order = _on_order_by_model()
    needs: list[ConsumableNeed] = []
    for consumable in Consumable.objects.filter(quantity__lt=F("min_quantity")).select_related(
        "model__manufacturer", "model__default_supplier", "location__parent"
    ):
        ordered = on_order.get(consumable.model_id, 0)
        needs.append(
            {
                "consumable": consumable,
                "missing": consumable.min_quantity - consumable.quantity,
                "on_order": ordered,
                "to_order": max(consumable.min_quantity - consumable.quantity - ordered, 0),
            }
        )
    return needs

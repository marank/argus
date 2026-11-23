"""How many devices are left in the pool for a category or model, now or in a period."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from django.db.models import Count, F, Q, QuerySet, Sum
from django.utils import timezone

from apps.inventory.models import Asset, AssetStatus, Consumable, License

if TYPE_CHECKING:
    from apps.requests.models import AssetRequestItem


def _model_filter(category_id: UUID | None, model_id: UUID | None) -> dict[str, UUID]:
    """A model, or the category's own models: subcategories hold accessories, not "any device"."""
    if model_id:
        return {"model_id": model_id}
    if category_id:
        return {"model__category_id": category_id}
    return {}


def pool_assets(category_id: UUID | None = None, model_id: UUID | None = None) -> QuerySet[Asset]:
    """Serialized assets in stock that may be lent out."""
    return Asset.objects.filter(
        status=AssetStatus.IN_STOCK, is_loanable=True, **_model_filter(category_id, model_id)
    )


def pool_consumables(category_id: UUID | None = None, model_id: UUID | None = None) -> QuerySet[Consumable]:
    return Consumable.objects.filter(**_model_filter(category_id, model_id))


def pool_licenses(category_id: UUID | None = None, model_id: UUID | None = None) -> QuerySet[License]:
    """Licenses that have not expired and still have a free seat, fullest-term first."""
    return (
        License.objects.filter(**_model_filter(category_id, model_id))
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.localdate()))
        .annotate(used=Count("assignments"))
        .filter(used__lt=F("seats"))
        .select_related("model__manufacturer")
        .order_by("valid_until", "created_at")
    )


def free_license_seats(category_id: UUID | None = None, model_id: UUID | None = None) -> int:
    """Unassigned seats of licenses that have not expired."""
    licenses = (
        License.objects.filter(**_model_filter(category_id, model_id))
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.localdate()))
        .annotate(used=Count("assignments"))
    )
    return sum(max(license.seats - license.used, 0) for license in licenses)


def available_count(category_id: UUID | None = None, model_id: UUID | None = None) -> int:
    assets = pool_assets(category_id, model_id).count()
    bulk = (
        pool_consumables(category_id, model_id)
        .aggregate(total=Sum(F("quantity") - F("reserved_quantity")))
        .get("total")
        or 0
    )
    return assets + max(bulk, 0) + free_license_seats(category_id, model_id)


@dataclass
class Counts:
    """Free units in a period and units already promised to other requests.

    ``available + reserved`` is what IT holds right now (devices in stock or set
    aside, consumable stock, free license seats).
    """

    available: int = 0
    reserved: int = 0

    def add(self, other: Counts) -> None:
        self.available += other.available
        self.reserved += other.reserved


def _held_units() -> tuple[dict[UUID, int], dict[UUID, int]]:
    """Units IT holds per model (devices in stock or set aside, consumable stock, free
    license seats), and the consumable units reserved of them."""
    from apps.masterdata.models import AssetModel

    stock: dict[UUID, int] = defaultdict(int)
    reserved: dict[UUID, int] = defaultdict(int)
    held = Asset.objects.filter(is_loanable=True, status__in=[AssetStatus.IN_STOCK, AssetStatus.RESERVED])
    for row in held.values("model_id").annotate(n=Count("pk")):
        stock[row["model_id"]] += row["n"]
    for row in Consumable.objects.values("model_id").annotate(n=Sum("quantity"), r=Sum("reserved_quantity")):
        stock[row["model_id"]] += row["n"] or 0
        reserved[row["model_id"]] += row["r"] or 0
    licensed = AssetModel.objects.filter(tracking=AssetModel.Tracking.LICENSE).values_list("pk", flat=True)
    for model_id in licensed:
        stock[model_id] += free_license_seats(model_id=model_id)
    return stock, reserved


def _overlapping(start: date, end: date | None) -> Q:
    """Items of confirmed or ready requests whose period overlaps ``start``–``end``."""
    from apps.requests.models import AssetRequestStatus

    overlapping = Q(asset_request__status__in=[AssetRequestStatus.CONFIRMED, AssetRequestStatus.READY]) & (
        Q(asset_request__end_date__isnull=True) | Q(asset_request__end_date__gte=start)
    )
    if end is not None:
        # Devices leave on the pickup day, which can be before they are needed.
        overlapping &= (
            Q(asset_request__start_date__lte=end)
            | Q(asset_request__requested_pickup_date__lte=end)
            | Q(asset_request__pickup_at__date__lte=end)
        )
    return overlapping


def _reserve_items(items: QuerySet[AssetRequestItem], reserved: dict[UUID, int]) -> dict[UUID, int]:
    """Adds the devices allocated to ``items`` and what they still lack of a model to
    ``reserved``; returns what they lack of any model, per category."""
    from apps.requests.models import AssetRequestAllocation

    any_reserved: dict[UUID, int] = defaultdict(int)
    allocated: dict[UUID, int] = defaultdict(int)
    for allocation in (
        AssetRequestAllocation.objects.filter(item__in=items, asset__isnull=False)
        .values("item_id", "asset__model_id")
        .annotate(n=Count("pk"))
    ):
        allocated[allocation["item_id"]] += allocation["n"]
        reserved[allocation["asset__model_id"]] += allocation["n"]
    consumable_allocated = dict(
        AssetRequestAllocation.objects.filter(item__in=items, consumable__isnull=False)
        .values_list("item_id")
        .annotate(n=Sum("quantity"))
    )
    for item in items:
        if item.is_software or item.is_free_text:
            continue
        lacking = max(item.quantity_target - allocated[item.pk] - consumable_allocated.get(item.pk, 0), 0)
        if item.asset_model_id:
            reserved[item.asset_model_id] += lacking
        elif item.category_id:
            any_reserved[item.category_id] += lacking
    return any_reserved


def period_availability(start: date, end: date | None) -> tuple[dict[UUID, Counts], dict[UUID, Counts]]:
    """Counts per model and per category (its own models only) for ``start``–``end``.

    ``end=None`` means from ``start`` on without end (permanent request). A request
    occupies its devices from the pickup day (wish or appointment) on. Reserved
    are units of confirmed or ready requests whose period overlaps: devices
    allocated to them plus what they still lack. Devices allocated to a request
    in another period count as available. Software is never reserved; licenses
    show their free seats.
    """
    from apps.masterdata.models import AssetModel
    from apps.requests.models import AssetRequestItem

    stock, reserved = _held_units()
    items = AssetRequestItem.objects.filter(_overlapping(start, end)).select_related(
        "asset_model", "category"
    )
    any_reserved = _reserve_items(items, reserved)

    models: dict[UUID, Counts] = {}
    categories: dict[UUID, Counts] = defaultdict(Counts)
    for model_id, category_id in AssetModel.objects.values_list("pk", "category_id"):
        held_units, promised = stock.get(model_id, 0), reserved.get(model_id, 0)
        models[model_id] = Counts(max(held_units - promised, 0), promised)
        categories[category_id].add(Counts(held_units, promised))
    for category_id, counts in categories.items():
        counts.reserved += any_reserved.get(category_id, 0)
        counts.available = max(counts.available - counts.reserved, 0)
    for category_id, lacking in any_reserved.items():
        if category_id not in categories:
            categories[category_id] = Counts(0, lacking)
    return models, dict(categories)

"""How many devices are left in the pool for a category or model, now or in a period."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.db.models import Count, F, Q, QuerySet, Sum
from django.utils import timezone

from apps.inventory.models import Asset, Consumable, License
from apps.masterdata.models import Category


def _model_filter(category_id: UUID | None, model_id: UUID | None) -> dict:
    if model_id:
        return {"model_id": model_id}
    if category_id:
        category = Category.objects.get(pk=category_id)
        return {"model__category_id__in": category.descendant_ids()}
    return {}


def pool_assets(category_id: UUID | None = None, model_id: UUID | None = None) -> QuerySet[Asset]:
    """Serialized assets in stock that may be lent out."""
    return Asset.objects.filter(
        status=Asset.Status.IN_STOCK, is_loanable=True, **_model_filter(category_id, model_id)
    )


def pool_consumables(category_id: UUID | None = None, model_id: UUID | None = None) -> QuerySet[Consumable]:
    return Consumable.objects.filter(**_model_filter(category_id, model_id))


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


def period_availability(start: date, end: date | None) -> tuple[dict[UUID, Counts], dict[UUID, Counts]]:
    """Counts per model and per category (its own models only) for ``start``–``end``.

    ``end=None`` means from ``start`` on without end (permanent request). Reserved
    are units of approved or ready requests whose period overlaps: devices
    allocated to them plus what they still lack. Devices allocated to a request
    in another period count as available. Software is never reserved; licenses
    show their free seats.
    """
    from apps.masterdata.models import AssetModel
    from apps.reservations.models import Reservation, ReservationAllocation, ReservationItem

    stock: dict[UUID, int] = defaultdict(int)
    reserved: dict[UUID, int] = defaultdict(int)
    any_reserved: dict[UUID, int] = defaultdict(int)

    held = Asset.objects.filter(is_loanable=True, status__in=[Asset.Status.IN_STOCK, Asset.Status.RESERVED])
    for row in held.values("model_id").annotate(n=Count("pk")):
        stock[row["model_id"]] += row["n"]
    for row in Consumable.objects.values("model_id").annotate(n=Sum("quantity"), r=Sum("reserved_quantity")):
        stock[row["model_id"]] += row["n"] or 0
        reserved[row["model_id"]] += row["r"] or 0

    overlapping = Q(reservation__status__in=[Reservation.Status.APPROVED, Reservation.Status.READY]) & (
        Q(reservation__end_date__isnull=True) | Q(reservation__end_date__gte=start)
    )
    if end is not None:
        overlapping &= Q(reservation__start_date__lte=end)
    items = ReservationItem.objects.filter(overlapping).select_related("asset_model", "category")
    allocated = defaultdict(int)
    for row in (
        ReservationAllocation.objects.filter(item__in=items, asset__isnull=False)
        .values("item_id", "asset__model_id")
        .annotate(n=Count("pk"))
    ):
        allocated[row["item_id"]] += row["n"]
        reserved[row["asset__model_id"]] += row["n"]
    consumable_allocated = dict(
        ReservationAllocation.objects.filter(item__in=items, consumable__isnull=False)
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

    licensed = AssetModel.objects.filter(tracking=AssetModel.Tracking.LICENSE).values_list("pk", flat=True)
    for model_id in licensed:
        stock[model_id] += free_license_seats(model_id=model_id)

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

"""How many devices are left in the pool for a category or model."""

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

"""Endpoints for the employee self-service portal."""

from uuid import UUID

from django.http import HttpRequest
from ninja import Router

from apps.core.api.security import is_it_staff
from apps.inventory.models import Asset
from apps.inventory.services.availability import available_count
from apps.masterdata.models import AssetModel, Category
from apps.reservations.models import ReservationAllocation
from apps.reservations.schemas.catalog import CatalogCategoryOut, MyAssetOut

router = Router(tags=["portal"])


@router.get("/catalog", response=list[CatalogCategoryOut])
def catalog(request: HttpRequest):
    """Requestable categories with their models.

    Availability counts are only included for IT staff; employees request what
    they need and IT decides what the pool can cover.
    """
    show_availability = is_it_staff(request.user)
    models_by_category: dict[UUID, list] = {}
    for model in AssetModel.objects.filter(is_requestable=True, is_active=True).select_related(
        "manufacturer"
    ):
        model.available = available_count(model_id=model.pk) if show_availability else None
        models_by_category.setdefault(model.category_id, []).append(model)

    result = []
    for category in Category.objects.filter(is_requestable=True):
        category.available = available_count(category_id=category.pk) if show_availability else None
        category.models = models_by_category.get(category.pk, [])
        result.append(category)
    return result


@router.get("/my-assets", response=list[MyAssetOut])
def my_assets(request: HttpRequest):
    """Devices currently handed out to the logged-in employee."""
    assets = Asset.objects.filter(assigned_to=request.user).select_related(
        "model__manufacturer", "model__category"
    )
    allocations = {
        a.asset_id: a.item.reservation
        for a in ReservationAllocation.objects.filter(
            asset__in=assets, returned_at__isnull=True
        ).select_related("item__reservation")
    }
    result = []
    for asset in assets:
        reservation = allocations.get(asset.pk)
        result.append(
            {
                "id": asset.pk,
                "inventory_number": asset.inventory_number,
                "serial_number": asset.serial_number,
                "model": asset.model,
                "category": asset.model.category.name,
                "assigned_since": asset.assigned_since.isoformat() if asset.assigned_since else None,
                "reservation_number": reservation.number if reservation else None,
                "return_due": (
                    reservation.end_date.isoformat() if reservation and reservation.end_date else None
                ),
            }
        )
    return result

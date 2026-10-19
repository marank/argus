from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, AssetEvent, StockMovement
from apps.inventory.services.events import log_event
from apps.inventory.services.stock import move_stock

Kind = AssetEvent.Kind


def _apply(asset: Asset, data: dict) -> None:
    for name, value in data.items():
        field = asset._meta.get_field(name)
        setattr(asset, f"{name}_id" if field.is_relation else name, value)


@transaction.atomic
def create_asset(data: dict, user) -> Asset:
    asset = Asset()
    _apply(asset, data)
    if asset.assigned_to_id:
        asset.status = Asset.Status.IN_USE
        asset.assigned_since = timezone.now()
    asset.full_clean(exclude=["inventory_number"])
    asset.save()
    log_event(asset, Kind.CREATED, user)
    if asset.assigned_to_id:
        log_event(asset, Kind.ASSIGNED, user, related_user_id=asset.assigned_to_id)
    return asset


@transaction.atomic
def update_asset(asset: Asset, data: dict, user) -> Asset:
    previous_status, previous_user = asset.status, asset.assigned_to_id
    _apply(asset, data)

    if asset.assigned_to_id != previous_user:
        if previous_user:
            log_event(asset, Kind.RETURNED, user, related_user_id=previous_user)
        if asset.assigned_to_id:
            asset.status = Asset.Status.IN_USE
            asset.assigned_since = timezone.now()
            log_event(asset, Kind.ASSIGNED, user, related_user_id=asset.assigned_to_id)
        else:
            asset.assigned_since = None
            if asset.status == Asset.Status.IN_USE:
                asset.status = Asset.Status.IN_STOCK

    if asset.status != previous_status:
        log_event(
            asset,
            Kind.STATUS_CHANGED,
            user,
            description=f"{Asset.Status(previous_status).label} → {asset.get_status_display()}",
        )
    asset.full_clean()
    asset.save()
    return asset


@transaction.atomic
def bulk_create_assets(common: dict, serial_numbers: list[str], user) -> list[Asset]:
    """Create one asset per scanned serial number with otherwise identical data."""
    serials = [s.strip() for s in serial_numbers if s.strip()]
    if len(set(serials)) != len(serials):
        raise BusinessError(_("The list contains duplicate serial numbers."))
    return [create_asset({**common, "serial_number": serial}, user) for serial in serials]


@transaction.atomic
def record_event(asset: Asset, data: dict, user, consume: dict | None = None) -> AssetEvent:
    """Record a manual event, optionally taking the spare part out of stock."""
    if data["kind"] not in AssetEvent.MANUAL_KINDS:
        raise BusinessError(_("This kind of event is recorded automatically."))
    event = log_event(asset, user=user, **data)
    if consume:
        from apps.inventory.models import StockItem

        stock_item = StockItem.objects.get(pk=consume["stock_item_id"])
        move_stock(
            stock_item,
            -consume["quantity"],
            StockMovement.Reason.CONSUMPTION,
            user,
            note=f"{asset.inventory_number}: {event.get_kind_display()}",
        )
    return event

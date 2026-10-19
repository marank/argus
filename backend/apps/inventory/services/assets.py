from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, AssetEvent, ConsumableMovement
from apps.inventory.services.consumables import move_consumable
from apps.inventory.services.events import log_event
from apps.masterdata.models import AssetModel

Kind = AssetEvent.Kind


def _apply(asset: Asset, data: dict) -> None:
    for name, value in data.items():
        field = asset._meta.get_field(name)
        setattr(asset, f"{name}_id" if field.is_relation else name, value)


def _set_consumables(asset: Asset, model_ids: list | None) -> None:
    """Assign consumables to the device; ``None`` leaves the assignment unchanged."""
    if model_ids is None:
        return
    found = list(AssetModel.objects.filter(pk__in=model_ids, tracking=AssetModel.Tracking.BULK))
    if len(found) != len(set(model_ids)):
        raise BusinessError(_("Only consumables can be assigned to a device."))
    asset.consumables.set(found)


@transaction.atomic
def create_asset(data: dict, user) -> Asset:
    data = dict(data)
    consumables = data.pop("consumables", None)
    asset = Asset()
    _apply(asset, data)
    if asset.assigned_to_id:
        asset.status = Asset.Status.IN_USE
        asset.assigned_since = timezone.now()
    asset.full_clean(exclude=["inventory_number"])
    asset.save()
    _set_consumables(asset, consumables)
    log_event(asset, Kind.CREATED, user)
    if asset.assigned_to_id:
        log_event(asset, Kind.ASSIGNED, user, related_user_id=asset.assigned_to_id)
    return asset


def _sync_reservation(asset: Asset, user) -> None:
    """Keep requests in step when a device is taken back or reassigned on the device page.

    A lent device counts as returned on its request (which completes once everything is
    back); a device set aside for a request must be released there first.
    """
    from apps.reservations.models import Reservation, ReservationAllocation
    from apps.reservations.services import workflow

    allocations = ReservationAllocation.objects.filter(asset=asset, returned_at__isnull=True)
    pending = allocations.filter(
        handed_out_at__isnull=True,
        item__reservation__status__in=[Reservation.Status.APPROVED, Reservation.Status.READY],
    ).select_related("item__reservation")
    if allocation := pending.first():
        raise BusinessError(
            _("%(asset)s is set aside for %(number)s. Remove it there first.")
            % {"asset": asset.inventory_number, "number": allocation.item.reservation.number}
        )
    lent = allocations.filter(
        handed_out_at__isnull=False, item__reservation__status=Reservation.Status.HANDED_OUT
    ).select_related("item__reservation")
    for allocation in lent:
        workflow.return_devices(allocation.item.reservation, user, [allocation.pk])
        asset.refresh_from_db()


@transaction.atomic
def update_asset(asset: Asset, data: dict, user) -> Asset:
    data = dict(data)
    if "assigned_to" in data and str(data["assigned_to"] or "") != str(asset.assigned_to_id or ""):
        _sync_reservation(asset, user)
    previous_status, previous_user = asset.status, asset.assigned_to_id
    consumables = data.pop("consumables", None)
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
    _set_consumables(asset, consumables)
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
    """Record a manual event, optionally booking the used consumable out."""
    if data["kind"] not in AssetEvent.MANUAL_KINDS:
        raise BusinessError(_("This kind of event is recorded automatically."))
    event = log_event(asset, user=user, **data)
    if consume:
        from apps.inventory.models import Consumable

        consumable = Consumable.objects.get(pk=consume["consumable_id"])
        move_consumable(
            consumable,
            -consume["quantity"],
            ConsumableMovement.Reason.CONSUMPTION,
            user,
            note=f"{asset.inventory_number}: {event.get_kind_display()}",
        )
    return event

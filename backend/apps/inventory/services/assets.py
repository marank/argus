from typing import TYPE_CHECKING, Any, TypedDict
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.core.exceptions import BusinessError
from apps.core.models import NumberSequence
from apps.inventory.models import Asset, AssetEvent, AssetEventKind, AssetStatus, ConsumableMovement
from apps.inventory.services.consumables import move_consumable
from apps.inventory.services.events import log_event
from apps.masterdata.models import AssetModel

if TYPE_CHECKING:
    from apps.requests.models import AssetRequestAllocation


def _apply(asset: Asset, data: dict[str, Any]) -> None:
    for name, value in data.items():
        field = asset._meta.get_field(name)
        setattr(asset, f"{name}_id" if field.is_relation else name, value)


def _set_consumables(asset: Asset, model_ids: list[UUID] | None) -> None:
    """Assign consumables to the device; ``None`` leaves the assignment unchanged."""
    if model_ids is None:
        return
    found = list(AssetModel.objects.filter(pk__in=model_ids, tracking=AssetModel.Tracking.BULK))
    if len(found) != len(set(model_ids)):
        raise BusinessError(_("Only consumables can be assigned to a device."))
    asset.consumables.set(found)


@transaction.atomic
def create_asset(data: dict[str, Any], user: User) -> Asset:
    data = dict(data)
    consumables = data.pop("consumables", None)
    asset = Asset()
    _apply(asset, data)
    if asset.assigned_to_id:
        asset.status = AssetStatus.IN_USE
        asset.assigned_since = timezone.now()
    asset.full_clean(exclude=["inventory_number"])
    asset.save()
    _set_consumables(asset, consumables)
    log_event(asset, AssetEventKind.CREATED, user)
    if asset.assigned_to_id:
        log_event(asset, AssetEventKind.ASSIGNED, user, related_user_id=asset.assigned_to_id)
    return asset


def _open_allocations(asset: Asset) -> QuerySet[AssetRequestAllocation]:
    from apps.requests.models import AssetRequestAllocation

    return AssetRequestAllocation.objects.filter(asset=asset, returned_at__isnull=True).select_related(
        "item__asset_request"
    )


def _sync_asset_request(asset: Asset, user: User) -> None:
    """Keep requests in step when a device is taken back or reassigned on the device page.

    A lent device counts as returned on its request (which completes once everything is
    back); a device set aside for a request must be released there first.
    """
    from apps.requests.services import workflow

    for allocation in _open_allocations(asset):
        workflow.release_from_elsewhere(allocation, user)
    asset.refresh_from_db()


def _guard_reserved_status(asset: Asset, status: str) -> None:
    """A device set aside for a request keeps its status until it is removed there."""
    if asset.status != AssetStatus.RESERVED or status == AssetStatus.RESERVED:
        return
    allocation = _open_allocations(asset).filter(handed_out_at__isnull=True).first()
    if allocation:
        raise BusinessError(
            _("%(asset)s is set aside for %(number)s. Remove it there first.")
            % {"asset": asset.inventory_number, "number": allocation.item.asset_request.number}
        )


@transaction.atomic
def update_asset(asset: Asset, data: dict[str, Any], user: User) -> Asset:
    data = dict(data)
    if "status" in data:
        _guard_reserved_status(asset, data["status"])
    if "assigned_to" in data and str(data["assigned_to"] or "") != str(asset.assigned_to_id or ""):
        _sync_asset_request(asset, user)
    previous_status, previous_user = asset.status, asset.assigned_to_id
    consumables = data.pop("consumables", None)
    _apply(asset, data)

    if asset.assigned_to_id != previous_user:
        if previous_user:
            log_event(asset, AssetEventKind.RETURNED, user, related_user_id=previous_user)
        if asset.assigned_to_id:
            asset.status = AssetStatus.IN_USE
            asset.assigned_since = timezone.now()
            log_event(asset, AssetEventKind.ASSIGNED, user, related_user_id=asset.assigned_to_id)
        else:
            asset.assigned_since = None
            if asset.status == AssetStatus.IN_USE:
                asset.status = AssetStatus.IN_STOCK

    if asset.status != previous_status:
        log_event(
            asset,
            AssetEventKind.STATUS_CHANGED,
            user,
            description=f"{AssetStatus(previous_status).label} → {asset.get_status_display()}",
        )
    asset.full_clean()
    asset.save()
    _set_consumables(asset, consumables)
    return asset


@transaction.atomic
def bulk_create_assets(common: dict[str, Any], serial_numbers: list[str], user: User) -> list[Asset]:
    """Create one asset per scanned serial number with otherwise identical data."""
    serials = [s.strip() for s in serial_numbers if s.strip()]
    if len(set(serials)) != len(serials):
        raise BusinessError(_("The list contains duplicate serial numbers."))
    return [create_asset({**common, "serial_number": serial}, user) for serial in serials]


def series_sequence(model: AssetModel) -> NumberSequence:
    """The number sequence a series of ``model`` draws from; series need one of their own."""
    sequence = model.effective_number_sequence()
    if sequence is None:
        raise BusinessError(
            _("Neither %(model)s nor its category has a number sequence. Assign one to create a series.")
            % {"model": model.full_name}
        )
    return sequence


class SeriesPreview(TypedDict):
    sequence: str
    first: str
    last: str


def preview_series(model: AssetModel, count: int) -> SeriesPreview:
    """The first and last inventory number a series of ``count`` devices would get."""
    sequence = series_sequence(model)
    start = 1 if sequence.period_key != sequence.current_period_key() else sequence.next_value
    return {
        "sequence": sequence.name,
        "first": sequence.format(start),
        "last": sequence.format(start + max(count, 1) - 1),
    }


@transaction.atomic
def create_series(common: dict[str, Any], count: int, user: User) -> list[Asset]:
    """Create ``count`` identical devices numbered in a row from the category's sequence."""
    series_sequence(AssetModel.objects.select_related("category", "manufacturer").get(pk=common["model"]))
    return [create_asset(common, user) for _ in range(count)]


@transaction.atomic
class Consumption(TypedDict):
    consumable_id: UUID
    quantity: int


def record_event(
    asset: Asset, data: dict[str, Any], user: User, consume: Consumption | None = None
) -> AssetEvent:
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

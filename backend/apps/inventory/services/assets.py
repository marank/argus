from contextlib import nullcontext
from typing import TYPE_CHECKING, Any, TypedDict
from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.activity.models import ActivityKind
from apps.activity.services import log as activity
from apps.core.exceptions import BusinessError
from apps.core.models import NumberSequence
from apps.core.services.numbering import next_number
from apps.inventory.models import (
    INACTIVE_STATUSES,
    Asset,
    AssetComponent,
    AssetEvent,
    AssetEventKind,
    AssetStatus,
    ConsumableMovement,
)
from apps.inventory.services.consumables import move_consumable
from apps.inventory.services.events import log_event
from apps.inventory.services.mac_address import normalize_mac_address
from apps.masterdata.models import AssetModel, ComponentType, DeviceNaming

if TYPE_CHECKING:
    from apps.requests.models import AssetRequestAllocation


def _apply(asset: Asset, data: dict[str, Any]) -> None:
    for name, value in data.items():
        if name == "mac_address":
            value = normalize_mac_address(value)
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


def _component_type(asset: Asset, type_id: UUID) -> ComponentType:
    """The part kind, if devices of the asset's category have it."""
    found = ComponentType.for_category(asset.model.category).filter(pk=type_id).first()
    if found is None:
        raise BusinessError(
            _("Devices of the category %(category)s have no part of this kind.")
            % {"category": asset.model.category.name}
        )
    return found


def _set_components(asset: Asset, entries: list[dict[str, Any]] | None) -> None:
    """Record the parts fitted now; ``None`` leaves them unchanged.

    The list stands for all tracked parts: kinds left out or without serial number and date
    are removed. A different serial number here corrects the record; a replacement goes
    through the service book (``record_event``), which keeps the previous one.
    """
    if entries is None:
        return
    keep: set[UUID] = set()
    for entry in entries:
        component_type = _component_type(asset, entry["component_type"])
        if component_type.pk in keep:
            raise BusinessError(_("Each kind of part can be fitted only once."))
        serial, installed_on = entry.get("serial_number", "").strip(), entry.get("installed_on")
        if not serial and not installed_on:
            continue
        AssetComponent.objects.update_or_create(
            asset=asset,
            component_type=component_type,
            defaults={"serial_number": serial, "installed_on": installed_on},
        )
        keep.add(component_type.pk)
    asset.installed_components.exclude(component_type__in=keep).delete()


def name_taken(name: str, exclude: UUID | None = None) -> bool:
    """Whether a device in use is already called ``name``, in any letter case (as hostnames)."""
    queryset = Asset.objects.filter(name__iexact=name).exclude(status__in=INACTIVE_STATUSES)
    if exclude is not None:
        queryset = queryset.exclude(pk=exclude)
    return queryset.exists()


def _give_name(asset: Asset) -> None:
    """A new device without a name gets the one its category provides, if any."""
    category = asset.model.category
    if asset.name or asset.status in INACTIVE_STATUSES:
        return
    match category.device_naming:
        case DeviceNaming.SEQUENCE if category.name_sequence:
            asset.name = next_number(category.name_sequence, taken=name_taken)
        case DeviceNaming.INVENTORY_NUMBER if not name_taken(asset.inventory_number):
            asset.name = asset.inventory_number
        case _:
            return
    asset.save(update_fields=["name", "updated_at"])


@transaction.atomic
def create_asset(data: dict[str, Any], user: User) -> Asset:
    data = dict(data)
    consumables = data.pop("consumables", None)
    components = data.pop("installed_components", None)
    asset = Asset()
    _apply(asset, data)
    if asset.assigned_to_id:
        asset.status = AssetStatus.IN_USE
        asset.assigned_since = timezone.now()
    asset.full_clean(exclude=["inventory_number"])
    asset.save()
    _give_name(asset)
    _set_consumables(asset, consumables)
    _set_components(asset, components)
    with activity.muted():
        log_event(asset, AssetEventKind.CREATED, user)
        if asset.assigned_to_id:
            log_event(asset, AssetEventKind.ASSIGNED, user, related_user_id=asset.assigned_to_id)
    activity.log(
        ActivityKind.ASSET_CREATED,
        asset.pk,
        activity.asset_label(asset),
        user,
        related_user_id=asset.assigned_to_id,
    )
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


def _change_holder(asset: Asset, previous_user: UUID | None, user: User) -> None:
    """Logs the return to ``previous_user`` and the hand-out to the new holder; sets the status."""
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


@transaction.atomic
def update_asset(asset: Asset, data: dict[str, Any], user: User) -> Asset:
    data = dict(data)
    if "status" in data:
        _guard_reserved_status(asset, data["status"])
    if "assigned_to" in data and str(data["assigned_to"] or "") != str(asset.assigned_to_id or ""):
        _sync_asset_request(asset, user)
    previous_status, previous_user = asset.status, asset.assigned_to_id
    consumables = data.pop("consumables", None)
    components = data.pop("installed_components", None)
    _apply(asset, data)

    if asset.assigned_to_id != previous_user:
        _change_holder(asset, previous_user, user)

    if asset.status != previous_status:
        # A new holder brings the status along; the activity log shows the hand-out alone.
        with activity.muted() if asset.assigned_to_id != previous_user else nullcontext():
            log_event(
                asset,
                AssetEventKind.STATUS_CHANGED,
                user,
                description=f"{AssetStatus(previous_status).label} → {asset.get_status_display()}",
            )
    asset.full_clean()
    asset.save()
    _set_consumables(asset, consumables)
    _set_components(asset, components)
    return asset


# What becomes of a device that another one replaces.
REPLACED_STATUSES = (AssetStatus.IN_STOCK, AssetStatus.IN_REPAIR, AssetStatus.RETIRED)


@transaction.atomic
def replace_asset(asset: Asset, replacement: Asset, status: str, user: User) -> Asset:
    """``replacement`` takes the place of ``asset``: its device name, holder and location.

    E.g. a new PC that keeps the hostname of the old one, or a spare MDE for one in repair.
    ``asset`` gives all three up and gets ``status``.
    """
    if replacement.pk == asset.pk:
        raise BusinessError(_("A device cannot replace itself."))
    if replacement.status != AssetStatus.IN_STOCK:
        raise BusinessError(
            _("Only a device in stock can be the replacement; %(asset)s is “%(status)s”.")
            % {"asset": replacement.inventory_number, "status": replacement.get_status_display()}
        )
    if status not in REPLACED_STATUSES:
        raise BusinessError(_("The replaced device can go into stock, into repair or be retired."))
    name, holder = asset.name, asset.assigned_to_id
    location = asset.location_id or replacement.location_id
    replaces = _("Replaces %(asset)s") % {"asset": asset.inventory_number}
    # One row in the activity log for the whole swap.
    with activity.muted():
        # The old device gives the name up first: only one device in use may have it.
        update_asset(asset, {"name": "", "assigned_to": None, "status": status}, user)
        update_asset(replacement, {"name": name, "assigned_to": holder, "location": location}, user)
        log_event(
            asset,
            AssetEventKind.REPLACED,
            user,
            related_asset=replacement,
            description=_("Replaced by %(asset)s") % {"asset": replacement.inventory_number},
        )
        log_event(replacement, AssetEventKind.REPLACED, user, related_asset=asset, description=replaces)
    activity.log(
        ActivityKind.ASSET_REPLACED,
        replacement.pk,
        activity.asset_label(replacement),
        user,
        related_user_id=holder,
        detail=replaces,
    )
    return replacement


@transaction.atomic
def bulk_create_assets(common: dict[str, Any], serial_numbers: list[str], user: User) -> list[Asset]:
    """Create one asset per scanned serial number with otherwise identical data."""
    serials = [s.strip() for s in serial_numbers if s.strip()]
    if len(set(serials)) != len(serials):
        raise BusinessError(_("The list contains duplicate serial numbers."))
    with activity.muted():
        assets = [create_asset({**common, "serial_number": serial}, user) for serial in serials]
    _log_created(assets, user)
    return assets


def _log_created(assets: list[Asset], user: User) -> None:
    """Devices created together are one row in the activity log."""
    if len(assets) == 1:
        activity.log(ActivityKind.ASSET_CREATED, assets[0].pk, activity.asset_label(assets[0]), user)
    elif assets:
        activity.log(
            ActivityKind.ASSETS_CREATED,
            None,
            assets[0].model.full_name,
            user,
            quantity=len(assets),
            detail=f"{assets[0].inventory_number} – {assets[-1].inventory_number}",
        )


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
    with activity.muted():
        assets = [create_asset(common, user) for _ in range(count)]
    _log_created(assets, user)
    return assets


class Consumption(TypedDict):
    consumable_id: UUID
    quantity: int


def _replace_component(asset: Asset, data: dict[str, Any]) -> None:
    """A tracked part was replaced: the device gets the new one, the event keeps the old serial."""
    component_type = _component_type(asset, data.pop("component_type"))
    part, _created = AssetComponent.objects.get_or_create(asset=asset, component_type=component_type)
    data["component_type_id"] = component_type.pk
    data["previous_serial"] = part.serial_number
    part.serial_number = data.get("component_serial", "").strip()
    occurred_at = data.get("occurred_at") or timezone.now()
    part.installed_on = timezone.localdate(occurred_at)
    part.save()


@transaction.atomic
def record_event(
    asset: Asset, data: dict[str, Any], user: User, consume: Consumption | None = None
) -> AssetEvent:
    """Record a manual event, optionally booking the used consumable out."""
    if data["kind"] not in AssetEvent.MANUAL_KINDS:
        raise BusinessError(_("This kind of event is recorded automatically."))
    data = dict(data)
    if data.get("component_type") and data["kind"] == AssetEventKind.COMPONENT_REPLACED:
        _replace_component(asset, data)
    else:
        # Only a replacement changes a tracked part.
        data.pop("component_type", None)
    event = log_event(asset, user=user, **data)
    if consume:
        from apps.inventory.models import Consumable

        consumable = Consumable.objects.get(pk=consume["consumable_id"])
        # Part of the device's event in the activity log.
        with activity.muted():
            move_consumable(
                consumable,
                -consume["quantity"],
                ConsumableMovement.Reason.CONSUMPTION,
                user,
                note=f"{asset.inventory_number}: {event.get_kind_display()}",
            )
    return event


@transaction.atomic
def delete_asset(asset: Asset, user: User) -> None:
    label = activity.asset_label(asset)
    asset.delete()
    activity.log(ActivityKind.ASSET_DELETED, None, label, user)

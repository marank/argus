"""State transitions of a reservation, from submission to return."""

from datetime import date, datetime
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.core.exceptions import BusinessError
from apps.core.models import SiteSettings
from apps.inventory.models import Asset, AssetEvent, Consumable, ConsumableMovement
from apps.inventory.services.availability import pool_assets, pool_consumables
from apps.inventory.services.consumables import move_consumable, release_consumable, reserve_consumable
from apps.inventory.services.events import log_event
from apps.masterdata.models import Category
from apps.reservations.models import Handover, Reservation, ReservationAllocation, ReservationItem
from apps.reservations.services import notifications

Status = Reservation.Status


def _require_status(reservation: Reservation, *allowed: str) -> None:
    if reservation.status not in allowed:
        raise BusinessError(
            _("This is not possible while the reservation is “%(status)s”.")
            % {"status": reservation.get_status_display()}
        )


def _validate_period(duration: str, start: date, end: date | None) -> None:
    if duration == Reservation.Duration.TEMPORARY:
        if end is None:
            raise BusinessError(_("Temporary reservations need an end date."))
        if end < start:
            raise BusinessError(_("The end date must not be before the start date."))
        limit = SiteSettings.load().max_loan_days
        if limit and (end - start).days + 1 > limit:
            raise BusinessError(_("Temporary requests can last at most %(days)s days.") % {"days": limit})


def _validate_pickup_wish(day: date | None, start: date) -> None:
    """The devices are collected before they are needed, but not in the past."""
    if day is None:
        return
    if day < timezone.localdate():
        raise BusinessError(_("The preferred pickup day must not be in the past."))
    if day > start:
        raise BusinessError(_("The preferred pickup day must not be after the day the devices are needed."))


# --- Employee actions --------------------------------------------------------


@transaction.atomic
def submit(requester, data: dict, items: list[dict], created_by) -> Reservation:
    if not items:
        raise BusinessError(_("Add at least one device to the request."))
    end_date = data.get("end_date") if data["duration"] == Reservation.Duration.TEMPORARY else None
    _validate_period(data["duration"], data["start_date"], end_date)
    _validate_pickup_wish(data.get("requested_pickup_date"), data["start_date"])

    reservation = Reservation.objects.create(
        requester=requester, created_by=created_by, **{**data, "end_date": end_date}
    )
    for position, item in enumerate(items):
        line = ReservationItem(
            reservation=reservation,
            position=position,
            category_id=item.get("category"),
            asset_model_id=item.get("asset_model"),
            description=(item.get("description") or "").strip(),
            quantity_requested=item["quantity"],
            note=item.get("note", ""),
        )
        line.full_clean()
        if line.category_id and not line.asset_model_id and not line.description:
            if not line.category.allow_any_model:
                raise BusinessError(
                    _("Please choose a specific model for “%(category)s”.") % {"category": line.category}
                )
        line.save()
    notifications.request_submitted(reservation)
    return reservation


@transaction.atomic
def cancel(reservation: Reservation, user) -> Reservation:
    _require_status(reservation, *Reservation.CANCELLABLE_STATUSES)
    _release_all(reservation)
    reservation.status = Status.CANCELLED
    reservation.completed_at = timezone.now()
    reservation.save()
    return reservation


# --- IT decisions ------------------------------------------------------------


@transaction.atomic
def approve(
    reservation: Reservation,
    user,
    quantities: dict[UUID, int],
    pickup_at: datetime | None,
    pickup_location_id: UUID | None,
    comment: str = "",
) -> Reservation:
    """Confirm a reservation, possibly with fewer devices than requested."""
    _require_status(reservation, Status.SUBMITTED, Status.APPROVED)
    # Editing an approved request again does not notify a second time.
    first_decision = reservation.status == Status.SUBMITTED
    for item in reservation.items.all():
        approved = quantities.get(item.pk, item.quantity_requested)
        if approved > item.quantity_requested:
            raise BusinessError(_("You cannot approve more devices than were requested."))
        if approved < item.quantity_allocated:
            raise BusinessError(
                _("Remove allocated devices of “%(item)s” before lowering the quantity.")
                % {"item": item.label}
            )
        item.quantity_approved = approved
        item.save(update_fields=["quantity_approved"])

    if not any(item.quantity_approved for item in reservation.items.all()):
        raise BusinessError(_("Approve at least one device or reject the request."))

    reservation.status = Status.APPROVED
    reservation.pickup_at = pickup_at
    reservation.pickup_location_id = pickup_location_id
    reservation.it_comment = comment
    reservation.handled_by = user
    reservation.approved_at = reservation.approved_at or timezone.now()
    reservation.save()
    if first_decision:
        notifications.request_decided(reservation)
    return reservation


@transaction.atomic
def reject(reservation: Reservation, user, comment: str) -> Reservation:
    _require_status(reservation, Status.SUBMITTED, Status.APPROVED)
    _release_all(reservation)
    reservation.status = Status.REJECTED
    reservation.it_comment = comment
    reservation.handled_by = user
    reservation.completed_at = timezone.now()
    reservation.save()
    notifications.request_decided(reservation)
    return reservation


@transaction.atomic
def reschedule(
    reservation: Reservation,
    user,
    pickup_at: datetime | None,
    pickup_location_id: UUID | None,
    handover_mode: str | None = None,
) -> Reservation:
    _require_status(reservation, Status.APPROVED, Status.READY)
    reservation.pickup_at = pickup_at
    reservation.pickup_location_id = pickup_location_id
    if handover_mode:
        reservation.handover_mode = handover_mode
    reservation.handled_by = user
    reservation.save()
    return reservation


@transaction.atomic
def resolve_item(item: ReservationItem, asset_model, user) -> ReservationItem:
    """Map a free-text line (or change an unallocated line) to a catalog model."""
    _require_status(item.reservation, Status.SUBMITTED, Status.APPROVED)
    if item.allocations.exists():
        raise BusinessError(_("Remove allocated devices before changing the model."))
    item.asset_model = asset_model
    item.category = asset_model.category
    item.save(update_fields=["asset_model", "category"])
    return item


# --- Preparation: binding concrete devices -----------------------------------


def _require_resolved(item: ReservationItem) -> None:
    if item.is_free_text:
        raise BusinessError(
            _("“%(item)s” is free text. Create or assign a model first.") % {"item": item.label}
        )


def _matches(item: ReservationItem, model) -> bool:
    _require_resolved(item)
    if item.asset_model_id:
        return model.pk == item.asset_model_id
    return model.category_id in Category.objects.get(pk=item.category_id).descendant_ids()


@transaction.atomic
def allocate_asset(item: ReservationItem, asset: Asset, user) -> ReservationAllocation:
    reservation = item.reservation
    _require_status(reservation, Status.APPROVED)
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if not _matches(item, asset.model):
        raise BusinessError(
            _("%(asset)s does not match “%(item)s”.") % {"asset": asset.inventory_number, "item": item.label}
        )
    if asset.status != Asset.Status.IN_STOCK:
        raise BusinessError(
            _("%(asset)s is not in stock (%(status)s).")
            % {"asset": asset.inventory_number, "status": asset.get_status_display()}
        )
    if item.quantity_missing < 1:
        raise BusinessError(
            _("All approved devices for “%(item)s” are already allocated.") % {"item": item.label}
        )

    asset.status = Asset.Status.RESERVED
    asset.save(update_fields=["status", "updated_at"])
    log_event(
        asset,
        AssetEvent.Kind.RESERVED,
        user,
        related_user=reservation.requester,
        reservation=reservation,
    )
    return ReservationAllocation.objects.create(item=item, asset=asset, allocated_by=user)


@transaction.atomic
def allocate_consumable(
    item: ReservationItem, consumable: Consumable, quantity: int, user
) -> ReservationAllocation:
    _require_status(item.reservation, Status.APPROVED)
    if not _matches(item, consumable.model):
        raise BusinessError(
            _("%(model)s does not match “%(item)s”.") % {"model": consumable.model, "item": item.label}
        )
    if quantity > item.quantity_missing:
        raise BusinessError(
            _("Only %(missing)s more units are needed for “%(item)s”.")
            % {"missing": item.quantity_missing, "item": item.label}
        )
    reserve_consumable(consumable, quantity)
    return ReservationAllocation.objects.create(
        item=item, consumable=consumable, quantity=quantity, allocated_by=user
    )


@transaction.atomic
def auto_allocate(reservation: Reservation, user) -> int:
    """Fill every open item from the pool; returns the number of units allocated."""
    _require_status(reservation, Status.APPROVED)
    allocated = 0
    for item in reservation.items.select_related("asset_model", "category"):
        if item.is_free_text:
            continue  # needs a decision by IT first
        filters = {"model_id": item.asset_model_id, "category_id": item.category_id}
        for asset in pool_assets(**filters).order_by("condition", "inventory_number"):
            if item.quantity_missing < 1:
                break
            allocate_asset(item, asset, user)
            allocated += 1
        for consumable in pool_consumables(**filters):
            missing = item.quantity_missing
            take = min(missing, consumable.available_quantity)
            if take > 0:
                allocate_consumable(item, consumable, take, user)
                allocated += take
    return allocated


@transaction.atomic
def remove_allocation(allocation: ReservationAllocation, user) -> None:
    reservation = allocation.item.reservation
    _require_status(reservation, Status.APPROVED, Status.READY)
    _release(allocation, user)
    allocation.delete()
    if reservation.status == Status.READY:
        reservation.status = Status.APPROVED
        reservation.save(update_fields=["status", "updated_at"])


def _release(allocation: ReservationAllocation, user) -> None:
    if allocation.asset_id:
        asset = allocation.asset
        if asset.status == Asset.Status.RESERVED:
            asset.status = Asset.Status.IN_STOCK
            asset.save(update_fields=["status", "updated_at"])
            log_event(
                asset,
                AssetEvent.Kind.STATUS_CHANGED,
                user,
                description=_("Released from %(number)s") % {"number": allocation.item.reservation.number},
            )
    else:
        release_consumable(allocation.consumable, allocation.quantity)


def _release_all(reservation: Reservation, user=None) -> None:
    for allocation in ReservationAllocation.objects.filter(
        item__reservation=reservation, handed_out_at__isnull=True
    ).select_related("asset", "consumable", "item__reservation"):
        _release(allocation, user)
        allocation.delete()


@transaction.atomic
def mark_ready(
    reservation: Reservation, user, handover_mode: str | None = None, skip_device_check: bool = False
) -> Reservation:
    """All devices are prepared. Pickup requests now show up on the pickup terminal."""
    _require_status(reservation, Status.APPROVED)
    missing = [item.label for item in reservation.items.all() if item.quantity_missing]
    if missing:
        raise BusinessError(_("Devices are still missing for: %(items)s") % {"items": ", ".join(missing)})
    if handover_mode:
        reservation.handover_mode = handover_mode
    reservation.skip_device_check = skip_device_check
    reservation.status = Status.READY
    reservation.handled_by = user
    reservation.save()
    notifications.request_ready(reservation)
    return reservation


@transaction.atomic
def reopen(reservation: Reservation, user) -> Reservation:
    """Back from ready to preparing, e.g. to change devices; allocations stay."""
    _require_status(reservation, Status.READY)
    reservation.status = Status.APPROVED
    reservation.handled_by = user
    reservation.save(update_fields=["status", "handled_by", "updated_at"])
    return reservation


# --- Hand-out and return -----------------------------------------------------

SIGNATURE_PREFIX = "data:image/png;base64,"
MAX_SIGNATURE_LENGTH = 600_000


def _validate_handover(method: str, received_by_name: str, signature: str) -> None:
    if method == Handover.Method.SIGNATURE:
        if not signature.startswith(SIGNATURE_PREFIX) or len(signature) > MAX_SIGNATURE_LENGTH:
            raise BusinessError(_("Please sign in the signature field."))
        if not received_by_name.strip():
            raise BusinessError(_("Enter who is collecting the devices."))
    elif signature:
        raise BusinessError(_("Only pickups at the terminal are signed."))


@transaction.atomic
def hand_out(
    reservation: Reservation,
    user,
    *,
    method: str = Handover.Method.DIRECT,
    received_by_id: UUID | None = None,
    received_by_name: str = "",
    signature: str = "",
    notes: str = "",
    location: str = "",
    allocation_notes: dict[UUID, str] | None = None,
) -> Reservation:
    """Hand all allocated devices to the requester and document the handover.

    The devices are always assigned to the requester, even if a colleague
    collects them; the collecting person is recorded on the handover.
    """
    _require_status(reservation, Status.READY)
    requester = reservation.requester
    if not received_by_id and not received_by_name.strip():
        received_by_id = requester.pk
    if received_by_id and not received_by_name.strip():
        received_by_name = User.objects.get(pk=received_by_id).display_name
    _validate_handover(method, received_by_name, signature)

    now = timezone.now()
    allocation_notes = allocation_notes or {}
    allocations = ReservationAllocation.objects.filter(item__reservation=reservation).select_related(
        "asset", "consumable"
    )
    for allocation in allocations:
        note = allocation_notes.get(allocation.pk, "").strip()
        if allocation.asset_id:
            asset = allocation.asset
            asset.status = Asset.Status.IN_USE
            asset.assigned_to = requester
            asset.assigned_since = now
            asset.save(update_fields=["status", "assigned_to", "assigned_since", "updated_at"])
            log_event(
                asset,
                AssetEvent.Kind.ASSIGNED,
                user,
                related_user=requester,
                reservation=reservation,
                description=note,
            )
        else:
            move_consumable(
                allocation.consumable,
                -allocation.quantity,
                ConsumableMovement.Reason.ISSUE,
                user,
                release_reserved=allocation.quantity,
                recipient=requester,
                reservation=reservation,
                note=f"{reservation.number} {note}".strip(),
            )
        allocation.handed_out_at = now
        allocation.handout_note = note
        allocation.save(update_fields=["handed_out_at", "handout_note"])

    Handover.objects.create(
        reservation=reservation,
        method=method,
        received_by_id=received_by_id,
        received_by_name=received_by_name.strip(),
        signature=signature,
        notes=notes.strip(),
        location=location.strip(),
        handed_out_by=user,
    )

    reservation.handed_out_at = now
    if method != Handover.Method.SIGNATURE:
        reservation.handled_by = user
    if reservation.duration == Reservation.Duration.PERMANENT:
        reservation.status = Status.COMPLETED
        reservation.completed_at = now
    else:
        reservation.status = Status.HANDED_OUT
    reservation.save()
    return reservation


@transaction.atomic
def return_devices(reservation: Reservation, user, allocation_ids: list[UUID] | None = None) -> Reservation:
    """Take back lent devices; completes the reservation once everything is back.

    Bulk items (consumables) are not expected back and count as returned.
    """
    _require_status(reservation, Status.HANDED_OUT)
    now = timezone.now()
    open_allocations = ReservationAllocation.objects.filter(
        item__reservation=reservation, returned_at__isnull=True
    ).select_related("asset")
    selected = open_allocations.filter(pk__in=allocation_ids) if allocation_ids else open_allocations

    for allocation in selected:
        if allocation.asset_id:
            asset = allocation.asset
            asset.status = Asset.Status.IN_STOCK
            asset.assigned_to = None
            asset.assigned_since = None
            asset.save(update_fields=["status", "assigned_to", "assigned_since", "updated_at"])
            log_event(
                asset,
                AssetEvent.Kind.RETURNED,
                user,
                related_user=reservation.requester,
                reservation=reservation,
            )
        allocation.returned_at = now
        allocation.save(update_fields=["returned_at"])

    if not open_allocations.filter(asset__isnull=False).exists():
        open_allocations.update(returned_at=now)
        reservation.status = Status.COMPLETED
        reservation.completed_at = now
    reservation.handled_by = user
    reservation.save()
    return reservation

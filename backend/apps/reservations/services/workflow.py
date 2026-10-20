"""State transitions of a reservation, from submission to return."""

from datetime import date, datetime
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.accounts.services import assignment
from apps.core.exceptions import BusinessError
from apps.core.models import SiteSettings
from apps.inventory.models import Asset, AssetEvent, Consumable, ConsumableMovement, License
from apps.inventory.services.availability import pool_assets, pool_consumables, pool_licenses
from apps.inventory.services.consumables import move_consumable, release_consumable, reserve_consumable
from apps.inventory.services.events import log_event
from apps.inventory.services.licenses import assign_license
from apps.reservations.models import (
    DeviceReturn,
    Handover,
    Reservation,
    ReservationAllocation,
    ReservationItem,
)
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
def submit(
    requester, data: dict, items: list[dict], created_by, *, allow_past_start: bool = False
) -> Reservation:
    """Create a request; ``allow_past_start`` is for recording history (demo data)."""
    if not items:
        raise BusinessError(_("Add at least one device to the request."))
    if data["start_date"] < timezone.localdate() and not allow_past_start:
        raise BusinessError(_("The start date must not be in the past."))
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
    reservation.assigned_team = assignment.route(_item_team(item) for item in reservation.items.all())
    if reservation.assigned_team:
        reservation.save(update_fields=["assigned_team", "updated_at"])
    notifications.request_submitted(reservation)
    return reservation


def _item_team(item: ReservationItem):
    """The team a request line routes to: its model's, else its category's."""
    if item.asset_model_id:
        return item.asset_model.effective_team()
    return item.category.effective_team() if item.category_id else None


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
def extend(reservation: Reservation, user, end_date: date) -> Reservation:
    """Move the return date of lent devices, e.g. instead of chasing an overdue return.

    IT decides here, so the maximum loan period for requests does not apply. Reminders
    follow the new date (they are keyed by it).
    """
    _require_status(reservation, Status.HANDED_OUT)
    if reservation.duration != Reservation.Duration.TEMPORARY:
        raise BusinessError(_("Only temporary reservations have a return date."))
    if end_date < timezone.localdate():
        raise BusinessError(_("The new return date must not be in the past."))
    if end_date <= reservation.end_date:
        raise BusinessError(_("The new return date must be after the current one."))
    reservation.end_date = end_date
    reservation.handled_by = user
    reservation.save(update_fields=["end_date", "handled_by", "updated_at"])
    return reservation


@transaction.atomic
def remind(reservation: Reservation, user) -> Reservation:
    """Email the employee to bring the lent devices back."""
    from apps.core.models import MailSettings
    from apps.core.notifications import mail_ready

    _require_status(reservation, Status.HANDED_OUT)
    if reservation.duration != Reservation.Duration.TEMPORARY:
        raise BusinessError(_("Only temporary reservations have a return date."))
    if not mail_ready(MailSettings.load()):
        raise BusinessError(_("Email is not set up, so no reminder can be sent."))
    requester = reservation.requester
    if not requester.can_be_reminded:
        raise BusinessError(
            _("%(name)s has no email address, so no reminder can be sent.") % {"name": requester.display_name}
        )
    notifications.return_requested(reservation, user)
    reservation.reminded_at = timezone.now()
    reservation.reminded_by = user
    reservation.save(update_fields=["reminded_at", "reminded_by", "updated_at"])
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
    if model.is_software != item.is_software:
        return False
    if item.asset_model_id:
        return model.pk == item.asset_model_id
    # "Any laptop" means the category's own models; subcategories hold accessories.
    return model.category_id == item.category_id


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
def allocate_license(
    item: ReservationItem, license: License, user, asset: Asset | None = None
) -> ReservationAllocation:
    """Give the requester a seat of ``license`` (or one of their devices, for device licenses)."""
    reservation = item.reservation
    _require_status(reservation, Status.APPROVED)
    if not _matches(item, license.model):
        raise BusinessError(
            _("%(model)s does not match “%(item)s”.") % {"model": license.model, "item": item.label}
        )
    if item.quantity_missing < 1:
        raise BusinessError(
            _("All approved licenses for “%(item)s” are already allocated.") % {"item": item.label}
        )
    if license.assign_to == License.AssignTo.DEVICE:
        if asset is None:
            raise BusinessError(_("This license is assigned to devices. Choose a device."))
        if asset.assigned_to_id != reservation.requester_id:
            raise BusinessError(
                _("%(asset)s is not used by %(name)s.")
                % {"asset": asset.inventory_number, "name": reservation.requester.display_name}
            )
        target = {"asset_id": asset.pk}
    else:
        target = {"user_id": reservation.requester_id}
    assignment = assign_license(license, user, note=reservation.number, **target)
    return ReservationAllocation.objects.create(
        item=item, license=license, license_assignment=assignment, allocated_by=user
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
        if item.is_software:
            # Seats for the person only; device licenses need IT to pick the device.
            for license in pool_licenses(**filters).filter(assign_to=License.AssignTo.USER):
                if item.quantity_missing < 1:
                    break
                if not license.assignments.filter(user=reservation.requester).exists():
                    allocate_license(item, license, user)
                    allocated += 1
            continue
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
    if allocation.license_id:
        if allocation.license_assignment_id:
            allocation.license_assignment.delete()
    elif allocation.asset_id:
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
    ).select_related("asset", "consumable", "license_assignment", "item__reservation"):
        _release(allocation, user)
        allocation.delete()


def _has_physical(reservation: Reservation) -> bool:
    """Something to collect or deliver: devices or consumables (license seats are not)."""
    return ReservationAllocation.objects.filter(item__reservation=reservation, license__isnull=True).exists()


@transaction.atomic
def mark_ready(
    reservation: Reservation, user, handover_mode: str | None = None, skip_device_check: bool = False
) -> Reservation:
    """All devices are prepared. Pickup requests now show up on the pickup terminal.

    Without anything to collect (only software), the request is handed out right away.
    """
    _require_status(reservation, Status.APPROVED)
    missing = [item.label for item in reservation.items.all() if item.quantity_missing]
    if missing:
        raise BusinessError(_("Devices are still missing for: %(items)s") % {"items": ", ".join(missing)})
    if handover_mode:
        reservation.handover_mode = handover_mode
    reservation.skip_device_check = skip_device_check
    reservation.status = Status.READY
    reservation.handled_by = user
    reservation.prepared_by = user
    reservation.save()
    notifications.request_ready(reservation)
    if not _has_physical(reservation):
        hand_out(reservation, user)
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
    handed_out_by_id: UUID | None = None,
) -> Reservation:
    """Hand all allocated devices to the requester and document the handover.

    The devices are always assigned to the requester, even if a colleague
    collects them; the collecting person is recorded on the handover. ``user``
    records it (at the terminal: the terminal account); the handover names
    ``handed_out_by_id`` as responsible, at the terminal by default whoever
    prepared the pickup.
    """
    _require_status(reservation, Status.READY)
    if method == Handover.Method.SIGNATURE:
        handed_out_by_id = handed_out_by_id or reservation.prepared_by_id or reservation.handled_by_id
        if handed_out_by_id and not User.objects.filter(pk=handed_out_by_id, is_staff=True).exists():
            raise BusinessError(_("Choose a member of the IT department."))
    else:
        handed_out_by_id = user.pk
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
        if allocation.license_id:
            pass  # the seat was assigned when it was allocated
        elif allocation.asset_id:
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
        handed_out_by_id=handed_out_by_id,
        recorded_by=user,
    )

    reservation.handed_out_at = now
    if method != Handover.Method.SIGNATURE:
        reservation.handled_by = user
    lent = any(allocation.is_returnable for allocation in allocations)
    if reservation.duration == Reservation.Duration.PERMANENT or not lent:
        reservation.status = Status.COMPLETED
        reservation.completed_at = now
    else:
        reservation.status = Status.HANDED_OUT
    reservation.save()
    return reservation


@transaction.atomic
def return_devices(
    reservation: Reservation,
    user,
    allocation_ids: list[UUID] | None = None,
    *,
    notes: str = "",
    allocation_notes: dict[UUID, str] | None = None,
    damaged: set[UUID] | None = None,
) -> Reservation:
    """Take back lent devices and license seats and document the return.

    Devices listed in ``damaged`` go to repair instead of back into stock. A
    temporary reservation completes once everything is back; consumables are
    not expected back. Permanently handed-out devices can be taken back as well.
    """
    _require_status(reservation, *Reservation.RETURNABLE_STATUSES)
    allocation_notes = allocation_notes or {}
    damaged = damaged or set()
    now = timezone.now()
    open_allocations = ReservationAllocation.objects.filter(
        item__reservation=reservation, returned_at__isnull=True, handed_out_at__isnull=False
    ).select_related("asset", "license_assignment")
    returnable = open_allocations.filter(Q(asset__isnull=False) | Q(license__isnull=False))
    selected = list(returnable.filter(pk__in=allocation_ids) if allocation_ids else returnable.all())
    if not selected:
        if reservation.status == Status.HANDED_OUT and not returnable.exists():
            # Only consumables were handed out: nothing comes back, the request is done.
            open_allocations.update(returned_at=now)
            reservation.status = Status.COMPLETED
            reservation.completed_at = now
            reservation.save()
            return reservation
        raise BusinessError(_("Nothing is left to take back."))

    record = DeviceReturn.objects.create(reservation=reservation, notes=notes.strip(), returned_by=user)
    for allocation in selected:
        note = allocation_notes.get(allocation.pk, "").strip()
        if allocation.asset_id:
            asset = allocation.asset
            broken = allocation.pk in damaged
            asset.status = Asset.Status.IN_REPAIR if broken else Asset.Status.IN_STOCK
            asset.assigned_to = None
            asset.assigned_since = None
            asset.save(update_fields=["status", "assigned_to", "assigned_since", "updated_at"])
            log_event(
                asset,
                AssetEvent.Kind.RETURNED,
                user,
                related_user=reservation.requester,
                reservation=reservation,
                description=note,
            )
            if broken:
                log_event(
                    asset,
                    AssetEvent.Kind.STATUS_CHANGED,
                    user,
                    description=_("Returned damaged from %(number)s") % {"number": reservation.number},
                )
        elif allocation.license_assignment_id:
            allocation.license_assignment.delete()
            allocation.license_assignment = None
        allocation.returned_at = now
        allocation.device_return = record
        allocation.return_note = note
        allocation.returned_damaged = bool(allocation.asset_id) and allocation.pk in damaged
        allocation.save(
            update_fields=[
                "returned_at",
                "device_return",
                "return_note",
                "returned_damaged",
                "license_assignment",
            ]
        )

    if reservation.status == Status.HANDED_OUT and not returnable.exists():
        open_allocations.update(returned_at=now)
        reservation.status = Status.COMPLETED
        reservation.completed_at = now
    reservation.handled_by = user
    reservation.save()
    return reservation


def release_from_elsewhere(allocation: ReservationAllocation, user) -> None:
    """A device or seat was taken back outside the request (device or license page).

    Allocations still being prepared must be removed on the request first; lent
    ones count as returned there.
    """
    reservation = allocation.item.reservation
    if allocation.handed_out_at is None:
        if reservation.status in (Status.APPROVED, Status.READY):
            raise BusinessError(
                _("This is set aside for %(number)s. Remove it there first.") % {"number": reservation.number}
            )
        return
    if allocation.returned_at is None and reservation.status in Reservation.RETURNABLE_STATUSES:
        return_devices(reservation, user, [allocation.pk])

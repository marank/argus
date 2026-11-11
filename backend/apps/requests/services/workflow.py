"""State transitions of a request, from submission to return."""

from datetime import date, datetime, time
from enum import Enum
from typing import Any, Final, Literal
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils import formats, timezone
from django.utils.translation import gettext as _

from apps.accounts.models import Team, User
from apps.accounts.services import assignment
from apps.core.exceptions import BusinessError
from apps.core.features import FeatureKey, is_enabled
from apps.core.models import SiteSettings
from apps.inventory.models import (
    Asset,
    AssetEventKind,
    AssetStatus,
    Consumable,
    ConsumableMovement,
    License,
)
from apps.inventory.services.availability import pool_assets, pool_consumables, pool_licenses
from apps.inventory.services.consumables import move_consumable, release_consumable, reserve_consumable
from apps.inventory.services.events import log_event
from apps.inventory.services.licenses import assign_license
from apps.masterdata.models import AssetModel, CategoryKind
from apps.requests.models import (
    AssetRequest,
    AssetRequestAllocation,
    AssetRequestEventKind,
    AssetRequestItem,
    AssetRequestStatus,
    DeviceReturn,
    Handover,
    HandoverMethod,
)
from apps.requests.services import notifications
from apps.requests.services.history import allocation_label, record

Approval = AssetRequest.Approval


class _Keep(Enum):
    KEEP = "keep"


# Leaves a field as it is, where ``None`` would clear it.
KEEP: Final = _Keep.KEEP


def _require_status(asset_request: AssetRequest, *allowed: str) -> None:
    if asset_request.status not in allowed:
        raise BusinessError(
            _("This is not possible while the request is “%(status)s”.")
            % {"status": asset_request.get_status_display()}
        )


def _validate_period(duration: str, start: date, end: date | None) -> None:
    if duration == AssetRequest.Duration.TEMPORARY:
        if end is None:
            raise BusinessError(_("Temporary requests need an end date."))
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


def _require_requestable(line: AssetRequestItem) -> None:
    """Employees can only request what the portal catalog offers them (``portal.catalog``)."""
    software_off = not is_enabled(FeatureKey.SOFTWARE_REQUESTS)
    model = line.asset_model
    categories = {c for c in (line.category, model.category if model else None) if c}
    model_offered = not model or (
        model.is_requestable
        and model.is_active
        and not (software_off and model.tracking == AssetModel.Tracking.LICENSE)
    )
    categories_offered = all(
        c.is_requestable and not (software_off and c.kind == CategoryKind.SOFTWARE) for c in categories
    )
    if not (model_offered and categories_offered):
        raise BusinessError(_("“%(item)s” cannot be requested.") % {"item": line.label})
    if model and not model.category.allows_specific_model:
        # IT picks the model when handing out; employees ask for any device of the category.
        raise BusinessError(
            _("For “%(category)s” IT picks the model; request any model instead.")
            % {"category": model.category}
        )


@transaction.atomic
def submit(
    requester: User,
    data: dict[str, Any],
    items: list[dict[str, Any]],
    created_by: User | None,
    *,
    allow_past_start: bool = False,
    from_catalog: bool = False,
) -> AssetRequest:
    """Create a request; ``allow_past_start`` is for recording history (demo data).

    With ``from_catalog`` (employees) every line must be on offer in the catalog; IT
    may record anything.
    """
    if not items:
        raise BusinessError(_("Add at least one device to the request."))
    if data["start_date"] < timezone.localdate() and not allow_past_start:
        raise BusinessError(_("The start date must not be in the past."))
    end_date = data.get("end_date") if data["duration"] == AssetRequest.Duration.TEMPORARY else None
    _validate_period(data["duration"], data["start_date"], end_date)
    _validate_pickup_wish(data.get("requested_pickup_date"), data["start_date"])

    asset_request = AssetRequest.objects.create(
        requester=requester, created_by=created_by, **{**data, "end_date": end_date}
    )
    _record_created(asset_request, AssetRequestEventKind.CREATED, created_by)
    for position, item in enumerate(items):
        line = AssetRequestItem(
            asset_request=asset_request,
            position=position,
            category_id=item.get("category"),
            asset_model_id=item.get("asset_model"),
            description=(item.get("description") or "").strip(),
            quantity_requested=item["quantity"],
            note=item.get("note", ""),
        )
        line.full_clean()
        if from_catalog:
            _require_requestable(line)
        if line.category and not line.asset_model_id and not line.description:
            if not line.category.allows_any_model:
                raise BusinessError(
                    _("Please choose a specific model for “%(category)s”.") % {"category": line.category}
                )
        line.save()
    asset_request.assigned_team = assignment.route(_item_team(item) for item in asset_request.items.all())
    if _needs_approval(asset_request, created_by):
        if asset_request.may_approve(requester):
            # An approver's own request is approved by asking for it.
            _record_approval(asset_request, requester, Approval.APPROVED)
        else:
            asset_request.status = AssetRequestStatus.PENDING_APPROVAL
            asset_request.approval = Approval.PENDING
    asset_request.save()
    if asset_request.status == AssetRequestStatus.PENDING_APPROVAL:
        notifications.approval_requested(asset_request)
    else:
        notifications.request_submitted(asset_request)
    return asset_request


def _needs_approval(asset_request: AssetRequest, created_by: User | None) -> bool:
    """Whether the request must wait for the department before IT gets it.

    Not for exempt employees, not for requests IT records on someone's behalf and
    not when the department has nobody to approve (then it goes straight to IT).
    """
    requester = asset_request.requester
    if requester.approval_exempt:
        return False
    if created_by is not None and created_by.pk != requester.pk and created_by.is_it_staff:
        return False
    if not any(item.requires_approval for item in asset_request.items.all()):
        return False
    return asset_request.approvers().exists()


def _record_created(asset_request: AssetRequest, kind: str, user: User | None) -> None:
    on_behalf = user is not None and user.pk != asset_request.requester_id
    record(
        asset_request,
        kind,
        user,
        requester=asset_request.requester.display_name if on_behalf else None,
        follows=asset_request.follows.number if asset_request.follows else None,
    )


def _record_approval(asset_request: AssetRequest, user: User, decision: str, comment: str = "") -> None:
    record(
        asset_request,
        AssetRequestEventKind.APPROVED if decision == Approval.APPROVED else AssetRequestEventKind.DECLINED,
        user,
        comment=comment,
    )
    asset_request.approval = decision
    asset_request.approver = user
    asset_request.approval_decided_at = timezone.now()
    asset_request.approval_comment = comment
    if decision == Approval.APPROVED:
        asset_request.status = AssetRequestStatus.SUBMITTED
    else:
        asset_request.status = AssetRequestStatus.REJECTED
        asset_request.completed_at = asset_request.approval_decided_at


def _item_team(item: AssetRequestItem) -> Team | None:
    """The team a request line routes to: its model's, else its category's."""
    if item.asset_model:
        return item.asset_model.effective_team()
    return item.category.effective_team() if item.category else None


@transaction.atomic
def cancel(asset_request: AssetRequest, user: User) -> AssetRequest:
    _require_status(asset_request, *AssetRequest.CANCELLABLE_STATUSES)
    _release_all(asset_request)
    asset_request.status = AssetRequestStatus.CANCELLED
    asset_request.completed_at = timezone.now()
    asset_request.save()
    record(asset_request, AssetRequestEventKind.CANCELLED, user)
    notifications.request_cancelled(asset_request, user)
    return asset_request


# --- Department approval -----------------------------------------------------


def _require_approver(asset_request: AssetRequest, user: User) -> None:
    _require_status(asset_request, AssetRequestStatus.PENDING_APPROVAL)
    if not asset_request.may_approve(user):
        raise BusinessError(_("Only an approver of the requester's department can decide on this request."))


@transaction.atomic
def approve(asset_request: AssetRequest, user: User, comment: str = "") -> AssetRequest:
    """The department agrees; from now on the request is IT's."""
    _require_approver(asset_request, user)
    _record_approval(asset_request, user, Approval.APPROVED, comment)
    asset_request.save()
    notifications.request_submitted(asset_request)
    return asset_request


@transaction.atomic
def decline(asset_request: AssetRequest, user: User, comment: str) -> AssetRequest:
    """The department refuses; IT never sees the request as work."""
    _require_approver(asset_request, user)
    _record_approval(asset_request, user, Approval.REJECTED, comment)
    asset_request.save()
    notifications.approval_declined(asset_request)
    return asset_request


# --- IT decisions ------------------------------------------------------------


@transaction.atomic
def confirm(
    asset_request: AssetRequest,
    user: User,
    quantities: dict[UUID, int],
    comment: str = "",
) -> AssetRequest:
    """Tell the employee their request is fine, possibly with fewer devices than requested.

    How and when the devices reach them is planned later, when marking it ready.
    """
    _require_status(asset_request, AssetRequestStatus.SUBMITTED, AssetRequestStatus.CONFIRMED)
    # Editing a confirmed request again does not notify a second time.
    first_decision = asset_request.status == AssetRequestStatus.SUBMITTED
    for item in asset_request.items.all():
        confirmed = quantities.get(item.pk, item.quantity_requested)
        if confirmed > item.quantity_requested:
            raise BusinessError(_("You cannot confirm more devices than were requested."))
        if confirmed < item.quantity_allocated:
            raise BusinessError(
                _("Remove allocated devices of “%(item)s” before lowering the quantity.")
                % {"item": item.label}
            )
        item.quantity_confirmed = confirmed
        item.save(update_fields=["quantity_confirmed"])

    if not any(item.quantity_confirmed for item in asset_request.items.all()):
        raise BusinessError(_("Confirm at least one device or reject the request."))

    asset_request.status = AssetRequestStatus.CONFIRMED
    asset_request.it_comment = comment
    asset_request.handled_by = user
    asset_request.confirmed_at = asset_request.confirmed_at or timezone.now()
    asset_request.save()
    if first_decision:
        record(asset_request, AssetRequestEventKind.CONFIRMED, user, comment=comment)
        notifications.request_decided(asset_request)
    return asset_request


@transaction.atomic
def reject(asset_request: AssetRequest, user: User, comment: str) -> AssetRequest:
    _require_status(asset_request, AssetRequestStatus.SUBMITTED, AssetRequestStatus.CONFIRMED)
    _release_all(asset_request)
    asset_request.status = AssetRequestStatus.REJECTED
    asset_request.it_comment = comment
    asset_request.handled_by = user
    asset_request.completed_at = timezone.now()
    asset_request.save()
    record(asset_request, AssetRequestEventKind.REJECTED, user, comment=comment)
    notifications.request_decided(asset_request)
    return asset_request


@transaction.atomic
def reschedule(
    asset_request: AssetRequest,
    user: User,
    pickup_at: datetime | None,
    pickup_location_id: UUID | None,
    handover_mode: str | None = None,
    notify: bool = True,
) -> AssetRequest:
    """Change how, when or where; once the employee was told it is ready, ``notify`` tells them again."""
    _require_status(asset_request, AssetRequestStatus.CONFIRMED, AssetRequestStatus.READY)
    asset_request.pickup_at = pickup_at
    asset_request.pickup_location_id = pickup_location_id
    if handover_mode:
        asset_request.handover_mode = handover_mode
    # The employee hears of the handover once it is ready; before that there is nothing to correct.
    ready = asset_request.status == AssetRequestStatus.READY
    if ready and notify:
        _require_handover_plan(asset_request)
    asset_request.handled_by = user
    asset_request.save()
    asset_request.refresh_from_db(fields=["pickup_location"])
    _record_schedule(
        asset_request,
        AssetRequestEventKind.RESCHEDULED,
        user,
        notified=False if ready and not notify else None,
    )
    if ready and notify:
        notifications.request_rescheduled(asset_request)
    return asset_request


def _require_handover_plan(asset_request: AssetRequest) -> None:
    """A message to the employee must say when, and unless IT delivers, where."""
    if asset_request.handover_mode == AssetRequest.HandoverMode.DELIVERY:
        if not asset_request.pickup_at:
            raise BusinessError(_("Set the delivery date, or do not notify the employee."))
    elif not asset_request.pickup_at or not asset_request.pickup_location_id:
        raise BusinessError(_("Set date and place of the pickup, or do not notify the employee."))


def _record_schedule(asset_request: AssetRequest, kind: str, user: User, **extra: object) -> None:
    """A step that sets how and when the devices reach the employee."""
    record(
        asset_request,
        kind,
        user,
        handover_mode=asset_request.handover_mode,
        pickup_at=asset_request.pickup_at.isoformat() if asset_request.pickup_at else None,
        pickup_location=asset_request.pickup_location.full_name if asset_request.pickup_location else None,
        **extra,
    )


@transaction.atomic
def extend(asset_request: AssetRequest, user: User, end_date: date) -> AssetRequest:
    """Move the return date of lent devices, e.g. instead of chasing an overdue return.

    IT decides here, so the maximum loan period for requests does not apply. Reminders
    follow the new date (they are keyed by it).
    """
    _require_status(asset_request, AssetRequestStatus.HANDED_OUT)
    if asset_request.duration != AssetRequest.Duration.TEMPORARY:
        raise BusinessError(_("Only temporary requests have a return date."))
    if end_date < timezone.localdate():
        raise BusinessError(_("The new return date must not be in the past."))
    assert asset_request.end_date is not None  # _validate_period: temporary requests have one
    if end_date <= asset_request.end_date:
        raise BusinessError(_("The new return date must be after the current one."))
    previous = asset_request.end_date
    record(
        asset_request,
        AssetRequestEventKind.EXTENDED,
        user,
        previous=previous.isoformat(),
        end_date=end_date.isoformat(),
    )
    asset_request.end_date = end_date
    asset_request.handled_by = user
    asset_request.save(update_fields=["end_date", "handled_by", "updated_at"])
    notifications.request_extended(asset_request, previous)
    return asset_request


@transaction.atomic
def assign(
    asset_request: AssetRequest, team_id: UUID | None, assignee_id: UUID | None, user: User
) -> AssetRequest:
    """Hand the request to a team and/or person; recorded in the history when it changed."""
    before = (asset_request.assigned_team_id, asset_request.assignee_id)
    notify = assignment.assign(asset_request, team_id, assignee_id, user)
    if (asset_request.assigned_team_id, asset_request.assignee_id) != before:
        record(
            asset_request,
            AssetRequestEventKind.ASSIGNED,
            user,
            team=asset_request.assigned_team.name if asset_request.assigned_team else None,
            assignee=asset_request.assignee.display_name if asset_request.assignee else None,
        )
    if notify:
        notifications.request_assigned(asset_request)
    return asset_request


@transaction.atomic
def remind(asset_request: AssetRequest, user: User) -> AssetRequest:
    """Email the employee to bring the lent devices back."""
    from apps.core.models import MailSettings
    from apps.core.notifications import mail_ready

    _require_status(asset_request, AssetRequestStatus.HANDED_OUT)
    if asset_request.duration != AssetRequest.Duration.TEMPORARY:
        raise BusinessError(_("Only temporary requests have a return date."))
    if not mail_ready(MailSettings.load()):
        raise BusinessError(_("Email is not set up, so no reminder can be sent."))
    requester = asset_request.requester
    if not requester.can_be_reminded:
        raise BusinessError(
            _("%(name)s has no email address, so no reminder can be sent.") % {"name": requester.display_name}
        )
    notifications.return_requested(asset_request, user)
    asset_request.reminded_at = timezone.now()
    asset_request.reminded_by = user
    asset_request.save(update_fields=["reminded_at", "reminded_by", "updated_at"])
    record(asset_request, AssetRequestEventKind.REMINDED, user)
    return asset_request


@transaction.atomic
def resolve_item(item: AssetRequestItem, asset_model: AssetModel, user: User) -> AssetRequestItem:
    """Map a free-text line (or change an unallocated line) to a catalog model."""
    _require_status(item.asset_request, AssetRequestStatus.SUBMITTED, AssetRequestStatus.CONFIRMED)
    if item.allocations.exists():
        raise BusinessError(_("Remove allocated devices before changing the model."))
    item.asset_model = asset_model
    item.category = asset_model.category
    item.save(update_fields=["asset_model", "category"])
    return item


# --- Preparation: binding concrete devices -----------------------------------


def _require_resolved(item: AssetRequestItem) -> None:
    if item.is_free_text:
        raise BusinessError(
            _("“%(item)s” is free text. Create or assign a model first.") % {"item": item.label}
        )


def _matches(item: AssetRequestItem, model: AssetModel) -> bool:
    _require_resolved(item)
    if model.is_software != item.is_software:
        return False
    if item.asset_model_id:
        return model.pk == item.asset_model_id
    # "Any laptop" means the category's own models; subcategories hold accessories.
    return model.category_id == item.category_id


def _lock_item(item: AssetRequestItem) -> AssetRequestItem:
    """The line read again under a lock (request first, then line).

    Concurrent allocations to the same line wait here and then see what the other
    one allocated, so a line is never filled beyond its confirmed quantity.
    """
    asset_request = AssetRequest.objects.select_for_update().get(pk=item.asset_request_id)
    item = AssetRequestItem.objects.select_for_update().get(pk=item.pk)
    item.asset_request = asset_request
    return item


def _records_late(asset_request: AssetRequest) -> bool:
    """Handed out without devices: what IT allocates now is recorded as handed out back then."""
    return asset_request.devices_unrecorded and asset_request.status in AssetRequest.RETURNABLE_STATUSES


def _require_allocatable(asset_request: AssetRequest) -> None:
    if not _records_late(asset_request):
        _require_status(asset_request, AssetRequestStatus.CONFIRMED)


def _hand_out_late(allocation: AssetRequestAllocation, user: User) -> AssetRequestAllocation:
    """A device (or consumable, or seat) recorded after a hand-out without devices.

    The employee has had it since the hand-out, so it counts as handed out then. Once every
    line has its devices, nothing is left unrecorded.
    """
    asset_request = allocation.item.asset_request
    requester = asset_request.requester
    since = asset_request.handed_out_at or timezone.now()
    if allocation.asset:
        asset = allocation.asset
        asset.status = AssetStatus.IN_USE
        asset.assigned_to = requester
        asset.assigned_since = since
        asset.save(update_fields=["status", "assigned_to", "assigned_since", "updated_at"])
        log_event(
            asset,
            AssetEventKind.ASSIGNED,
            user,
            related_user=requester,
            asset_request=asset_request,
            description=_("Recorded after the hand-out of %(number)s") % {"number": asset_request.number},
        )
    elif allocation.consumable:
        move_consumable(
            allocation.consumable,
            -allocation.quantity,
            ConsumableMovement.Reason.ISSUE,
            user,
            release_reserved=allocation.quantity,
            recipient=requester,
            asset_request=asset_request,
            note=asset_request.number,
        )
    allocation.handed_out_at = since
    allocation.save(update_fields=["handed_out_at"])
    record(asset_request, AssetRequestEventKind.ALLOCATED, user, items=[allocation_label(allocation)])
    if not any(item.quantity_missing for item in asset_request.items.all()):
        asset_request.devices_unrecorded = False
        asset_request.save(update_fields=["devices_unrecorded", "updated_at"])
    return allocation


@transaction.atomic
def allocate_asset(item: AssetRequestItem, asset: Asset, user: User) -> AssetRequestAllocation:
    item = _lock_item(item)
    asset_request = item.asset_request
    _require_allocatable(asset_request)
    asset = Asset.objects.select_for_update().get(pk=asset.pk)
    if not _matches(item, asset.model):
        raise BusinessError(
            _("%(asset)s does not match “%(item)s”.") % {"asset": asset.inventory_number, "item": item.label}
        )
    if asset.status != AssetStatus.IN_STOCK:
        raise BusinessError(
            _("%(asset)s is not in stock (%(status)s).")
            % {"asset": asset.inventory_number, "status": asset.get_status_display()}
        )
    if item.quantity_missing < 1:
        raise BusinessError(
            _("All confirmed devices for “%(item)s” are already allocated.") % {"item": item.label}
        )

    # Set aside only: the device's history starts with the hand-out, the request's lists
    # the devices once it is ready.
    asset.status = AssetStatus.RESERVED
    asset.save(update_fields=["status", "updated_at"])
    allocation = AssetRequestAllocation.objects.create(item=item, asset=asset, allocated_by=user)
    return _hand_out_late(allocation, user) if _records_late(asset_request) else allocation


def _open_device_lines(asset_request: AssetRequest) -> list[AssetRequestItem]:
    """Lines that still take devices: resolved, not software, not filled."""
    return [
        item
        for item in asset_request.items.select_related("asset_model", "category").order_by("position")
        if not item.is_free_text and not item.is_software and item.quantity_missing
    ]


def line_for(asset_request: AssetRequest, asset: Asset) -> AssetRequestItem:
    """The open line a scanned device belongs to.

    A line for its exact model comes before one for any model of its category, so
    "any laptop" does not take the ThinkPad someone asked for by name.
    """
    lines = [item for item in _open_device_lines(asset_request) if _matches(item, asset.model)]
    if not lines:
        raise BusinessError(
            _("%(asset)s (%(model)s) matches no open line of this request.")
            % {"asset": asset.inventory_number, "model": asset.model}
        )
    return min(lines, key=lambda item: item.asset_model_id is None)


@transaction.atomic
def allocate_scanned(asset_request: AssetRequest, asset: Asset, user: User) -> AssetRequestAllocation:
    """Allocate a device to whichever open line it belongs to (one scan field for all lines)."""
    _require_allocatable(asset_request)
    return allocate_asset(line_for(asset_request, asset), asset, user)


@transaction.atomic
def allocate_consumable(
    item: AssetRequestItem, consumable: Consumable, quantity: int, user: User
) -> AssetRequestAllocation:
    item = _lock_item(item)
    _require_allocatable(item.asset_request)
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
    allocation = AssetRequestAllocation.objects.create(
        item=item, consumable=consumable, quantity=quantity, allocated_by=user
    )
    return _hand_out_late(allocation, user) if _records_late(item.asset_request) else allocation


@transaction.atomic
def allocate_license(
    item: AssetRequestItem, license: License, user: User, asset: Asset | None = None
) -> AssetRequestAllocation:
    """Give the requester a seat of ``license`` (or one of their devices, for device licenses)."""
    item = _lock_item(item)
    asset_request = item.asset_request
    _require_allocatable(asset_request)
    if not _matches(item, license.model):
        raise BusinessError(
            _("%(model)s does not match “%(item)s”.") % {"model": license.model, "item": item.label}
        )
    if item.quantity_missing < 1:
        raise BusinessError(
            _("All confirmed licenses for “%(item)s” are already allocated.") % {"item": item.label}
        )
    if license.assign_to == License.AssignTo.DEVICE:
        if asset is None:
            raise BusinessError(_("This license is assigned to devices. Choose a device."))
        if asset.assigned_to_id != asset_request.requester_id:
            raise BusinessError(
                _("%(asset)s is not used by %(name)s.")
                % {"asset": asset.inventory_number, "name": asset_request.requester.display_name}
            )
        target = {"asset_id": asset.pk}
    else:
        target = {"user_id": asset_request.requester_id}
    assignment = assign_license(license, user, note=asset_request.number, **target)
    allocation = AssetRequestAllocation.objects.create(
        item=item, license=license, license_assignment=assignment, allocated_by=user
    )
    return _hand_out_late(allocation, user) if _records_late(asset_request) else allocation


@transaction.atomic
def auto_allocate(asset_request: AssetRequest, user: User, item_id: UUID | None = None) -> int:
    """Fill every open item (or just the given one) from the pool; returns the units allocated."""
    _require_status(asset_request, AssetRequestStatus.CONFIRMED)
    items = asset_request.items.select_related("asset_model", "category")
    if item_id:
        items = items.filter(pk=item_id)
    allocated = 0
    for item in items:
        if item.is_free_text:
            continue  # needs a decision by IT first
        filters = {"model_id": item.asset_model_id, "category_id": item.category_id}
        if item.is_software:
            # Seats for the person only; device licenses need IT to pick the device.
            for license in pool_licenses(**filters).filter(assign_to=License.AssignTo.USER):
                if item.quantity_missing < 1:
                    break
                if not license.assignments.filter(user=asset_request.requester).exists():
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
def remove_allocation(allocation: AssetRequestAllocation, user: User) -> None:
    asset_request = allocation.item.asset_request
    _require_status(asset_request, AssetRequestStatus.CONFIRMED, AssetRequestStatus.READY)
    # Not noted: marking it ready again lists what changed.
    _release(allocation, user)
    allocation.delete()
    if asset_request.status == AssetRequestStatus.READY:
        asset_request.status = AssetRequestStatus.CONFIRMED
        asset_request.save(update_fields=["status", "updated_at"])
        record(asset_request, AssetRequestEventKind.REOPENED, user)


def _release(allocation: AssetRequestAllocation, user: User | None) -> None:
    """Give back what was set aside; the device was never handed out, so its history stays as it is."""
    if allocation.license_id:
        if allocation.license_assignment:
            allocation.license_assignment.delete()
    elif allocation.asset:
        asset = allocation.asset
        if asset.status == AssetStatus.RESERVED:
            asset.status = AssetStatus.IN_STOCK
            asset.save(update_fields=["status", "updated_at"])
    else:
        assert allocation.consumable is not None  # clean(): exactly one of asset, consumable, license
        release_consumable(allocation.consumable, allocation.quantity)


def _release_all(asset_request: AssetRequest, user: User | None = None) -> None:
    for allocation in AssetRequestAllocation.objects.filter(
        item__asset_request=asset_request, handed_out_at__isnull=True
    ).select_related("asset", "consumable", "license_assignment", "item__asset_request"):
        _release(allocation, user)
        allocation.delete()


def _has_physical(asset_request: AssetRequest) -> bool:
    """Something to collect or deliver: devices or consumables (license seats are not)."""
    return AssetRequestAllocation.objects.filter(
        item__asset_request=asset_request, license__isnull=True
    ).exists()


@transaction.atomic
def mark_ready(
    asset_request: AssetRequest,
    user: User,
    handover_mode: str | None = None,
    skip_device_check: bool = False,
    *,
    pickup_at: datetime | None | Literal[_Keep.KEEP] = KEEP,
    pickup_location_id: UUID | None | Literal[_Keep.KEEP] = KEEP,
    notify: bool = True,
) -> AssetRequest:
    """All devices are prepared. Pickup requests now show up on the pickup terminal.

    This is where IT sets how, when and where the devices reach the employee; date and
    place left out stay as they are. ``notify`` sends the ready message; IT turns it off
    e.g. for a direct hand-out it does right away. Without anything to collect (only
    software), the request is handed out right away.
    """
    _require_status(asset_request, AssetRequestStatus.CONFIRMED)
    missing = [item.label for item in asset_request.items.all() if item.quantity_missing]
    if missing:
        raise BusinessError(_("Devices are still missing for: %(items)s") % {"items": ", ".join(missing)})
    if handover_mode:
        asset_request.handover_mode = handover_mode
    if pickup_at is not KEEP:
        asset_request.pickup_at = pickup_at
    if pickup_location_id is not KEEP:
        asset_request.pickup_location_id = pickup_location_id
    asset_request.skip_device_check = skip_device_check
    if notify and _has_physical(asset_request):
        _require_handover_plan(asset_request)
    asset_request.status = AssetRequestStatus.READY
    asset_request.handled_by = user
    asset_request.prepared_by = user
    asset_request.save()
    asset_request.refresh_from_db(fields=["pickup_location"])
    # Only a skipped message is worth noting; sending it is the normal case.
    _record_schedule(
        asset_request,
        AssetRequestEventKind.READY,
        user,
        notified=None if notify else False,
        **_ready_items(asset_request),
    )
    if notify:
        notifications.request_ready(asset_request)
    if not _has_physical(asset_request):
        hand_out(asset_request, user)
    return asset_request


def _ready_items(asset_request: AssetRequest) -> dict[str, list[str]]:
    """What a ready step notes about the allocation.

    Allocating while preparing is not noted step by step (scanning, taking out, scanning
    again); the first time it is ready lists everything, a later time only what changed.
    ``allocated`` keeps the whole list to compare with next time.
    """
    current = [
        allocation_label(a)
        for a in AssetRequestAllocation.objects.filter(item__asset_request=asset_request)
        .select_related("asset", "consumable", "license")
        .order_by("item__position", "allocated_at")
    ]
    earlier = asset_request.events.filter(kind=AssetRequestEventKind.READY).order_by("-at").first()
    before = (earlier.data.get("allocated") or earlier.data.get("items")) if earlier else None
    if before is None:
        return {"items": current, "allocated": current}
    remaining = list(before)
    added: list[str] = []
    for label in current:
        if label in remaining:
            remaining.remove(label)
        else:
            added.append(label)
    return {"added": added, "removed": remaining, "allocated": current}


@transaction.atomic
def reopen(asset_request: AssetRequest, user: User) -> AssetRequest:
    """Back from ready to preparing, e.g. to change devices; allocations stay."""
    _require_status(asset_request, AssetRequestStatus.READY)
    asset_request.status = AssetRequestStatus.CONFIRMED
    asset_request.handled_by = user
    asset_request.save(update_fields=["status", "handled_by", "updated_at"])
    record(asset_request, AssetRequestEventKind.REOPENED, user)
    return asset_request


# --- Hand-out and return -----------------------------------------------------

SIGNATURE_PREFIX = "data:image/png;base64,"
MAX_SIGNATURE_LENGTH = 600_000


def _validate_handover(method: str, received_by_name: str, signature: str) -> None:
    if method == HandoverMethod.SIGNATURE:
        if not signature.startswith(SIGNATURE_PREFIX) or len(signature) > MAX_SIGNATURE_LENGTH:
            raise BusinessError(_("Please sign in the signature field."))
        if not received_by_name.strip():
            raise BusinessError(_("Enter who is collecting the devices."))
    elif signature:
        raise BusinessError(_("Only pickups at the terminal are signed."))


@transaction.atomic
def hand_out(
    asset_request: AssetRequest,
    user: User,
    *,
    method: str = HandoverMethod.DIRECT,
    received_by_id: UUID | None = None,
    received_by_name: str = "",
    signature: str = "",
    notes: str = "",
    location: str = "",
    allocation_notes: dict[UUID, str] | None = None,
    handed_out_by_id: UUID | None = None,
) -> AssetRequest:
    """Hand all allocated devices to the requester and document the handover.

    The devices are always assigned to the requester, even if a colleague
    collects them; the collecting person is recorded on the handover. ``user``
    records it (at the terminal: the terminal account); the handover names
    ``handed_out_by_id`` as responsible, at the terminal by default whoever
    prepared the pickup.
    """
    _require_status(asset_request, AssetRequestStatus.READY)
    if Handover.objects.filter(asset_request=asset_request).exists():
        raise BusinessError(_("This request has already been handed out."))
    if method == HandoverMethod.SIGNATURE:
        if handed_out_by_id:
            # Chosen at the terminal: must be someone from IT who can still be named.
            if not User.objects.filter(
                pk=handed_out_by_id, is_active=True, is_staff=True, is_terminal=False
            ).exists():
                raise BusinessError(_("Choose a member of the IT department."))
        else:
            handed_out_by_id = asset_request.prepared_by_id or asset_request.handled_by_id
            if handed_out_by_id and not User.objects.filter(pk=handed_out_by_id, is_staff=True).exists():
                raise BusinessError(_("Choose a member of the IT department."))
    else:
        handed_out_by_id = user.pk
    return _record_hand_out(
        asset_request,
        user,
        method=method,
        received_by_id=received_by_id,
        received_by_name=received_by_name,
        signature=signature,
        notes=notes,
        location=location,
        allocation_notes=allocation_notes or {},
        handed_out_by_id=handed_out_by_id,
    )


@transaction.atomic
def hand_out_without_devices(asset_request: AssetRequest, user: User, *, notes: str = "") -> AssetRequest:
    """The devices went out outside the system, before IT prepared the request.

    What is allocated is handed out as usual; the lines still missing devices stay open,
    so IT can record the devices later (or mark them returned without). A temporary
    request waits for the return like any other.
    """
    _require_status(asset_request, AssetRequestStatus.CONFIRMED)
    if not any(item.quantity_missing for item in asset_request.items.all()):
        raise BusinessError(_("Every device is allocated: mark the request ready and hand it out."))
    asset_request.devices_unrecorded = True
    return _record_hand_out(
        asset_request,
        user,
        method=HandoverMethod.DIRECT,
        received_by_id=None,
        received_by_name="",
        signature="",
        notes=notes,
        location="",
        allocation_notes={},
        handed_out_by_id=user.pk,
    )


def _missing_labels(asset_request: AssetRequest) -> list[str]:
    """The lines still without devices, e.g. "2× ThinkPad T14"."""
    return [
        f"{item.quantity_missing}× {item.label}"
        for item in asset_request.items.all()
        if item.quantity_missing
    ]


def _lent_without_devices(asset_request: AssetRequest) -> bool:
    """A line without its devices that would come back: anything but consumables."""
    return any(
        item.quantity_missing and not (item.asset_model and item.asset_model.is_bulk)
        for item in asset_request.items.all()
    )


def _record_hand_out(
    asset_request: AssetRequest,
    user: User,
    *,
    method: str,
    received_by_id: UUID | None,
    received_by_name: str,
    signature: str,
    notes: str,
    location: str,
    allocation_notes: dict[UUID, str],
    handed_out_by_id: UUID | None,
) -> AssetRequest:
    requester = asset_request.requester
    if received_by_id:
        # The requester always may; anyone else must be a current employee (not a terminal).
        received_by = (
            requester
            if received_by_id == requester.pk
            else User.objects.filter(pk=received_by_id, is_active=True, is_terminal=False).first()
        )
        if received_by is None:
            raise BusinessError(_("Choose an active employee as the person collecting the devices."))
        if not received_by_name.strip():
            received_by_name = received_by.display_name
    elif not received_by_name.strip():
        received_by_id = requester.pk
        received_by_name = requester.display_name
    _validate_handover(method, received_by_name, signature)

    now = timezone.now()
    allocation_notes = allocation_notes or {}
    allocations = AssetRequestAllocation.objects.filter(item__asset_request=asset_request).select_related(
        "asset", "consumable"
    )
    for allocation in allocations:
        note = allocation_notes.get(allocation.pk, "").strip()
        if allocation.license_id:
            pass  # the seat was assigned when it was allocated
        elif allocation.asset:
            asset = allocation.asset
            asset.status = AssetStatus.IN_USE
            asset.assigned_to = requester
            asset.assigned_since = now
            asset.save(update_fields=["status", "assigned_to", "assigned_since", "updated_at"])
            log_event(
                asset,
                AssetEventKind.ASSIGNED,
                user,
                related_user=requester,
                asset_request=asset_request,
                description=note,
            )
        else:
            assert allocation.consumable is not None  # clean(): exactly one of asset, consumable, license
            move_consumable(
                allocation.consumable,
                -allocation.quantity,
                ConsumableMovement.Reason.ISSUE,
                user,
                release_reserved=allocation.quantity,
                recipient=requester,
                asset_request=asset_request,
                note=f"{asset_request.number} {note}".strip(),
            )
        allocation.handed_out_at = now
        allocation.handout_note = note
        allocation.save(update_fields=["handed_out_at", "handout_note"])

    Handover.objects.create(
        asset_request=asset_request,
        method=method,
        received_by_id=received_by_id,
        received_by_name=received_by_name.strip(),
        signature=signature,
        notes=notes.strip(),
        location=location.strip(),
        handed_out_by_id=handed_out_by_id,
        recorded_by=user,
    )

    record(
        asset_request,
        AssetRequestEventKind.HANDED_OUT,
        User.objects.filter(pk=handed_out_by_id).first() if handed_out_by_id else user,
        method=method,
        received_by=received_by_name.strip(),
        location=location.strip(),
        items=[allocation_label(a) for a in allocations],
        missing=_missing_labels(asset_request) if asset_request.devices_unrecorded else [],
    )
    asset_request.handed_out_at = now
    if method != HandoverMethod.SIGNATURE:
        asset_request.handled_by = user
    lent = any(allocation.is_returnable for allocation in allocations) or (
        asset_request.devices_unrecorded and _lent_without_devices(asset_request)
    )
    if asset_request.duration == AssetRequest.Duration.PERMANENT or not lent:
        asset_request.status = AssetRequestStatus.COMPLETED
        asset_request.completed_at = now
    else:
        asset_request.status = AssetRequestStatus.HANDED_OUT
    asset_request.save()
    # Handed out outside the system: the employee already has the devices, nothing to tell.
    if not asset_request.devices_unrecorded:
        notifications.request_handed_out(
            asset_request, [allocation_label(a) for a in allocations], received_by_name.strip()
        )
    return asset_request


@transaction.atomic
def prepare_direct(
    requester: User,
    user: User,
    data: dict[str, Any],
    *,
    assets: list[UUID],
    consumables: dict[UUID, int] | None = None,
) -> AssetRequest:
    """IT picks specific devices from stock for an employee, without a request first.

    ``data`` holds the same fields as a request (purpose, period, pickup wish).
    The request is recorded as confirmed with the devices allocated; IT then marks
    it ready and hands it out as usual. ``consumables`` maps each stock to the
    quantity taken.
    """
    consumables = consumables or {}
    if not assets and not consumables:
        raise BusinessError(_("Add at least one device to the request."))
    if data["start_date"] < timezone.localdate():
        raise BusinessError(_("The start date must not be in the past."))
    end_date = data.get("end_date") if data["duration"] == AssetRequest.Duration.TEMPORARY else None
    _validate_period(data["duration"], data["start_date"], end_date)
    _validate_pickup_wish(data.get("requested_pickup_date"), data["start_date"])

    asset_request = AssetRequest.objects.create(
        origin=AssetRequest.Origin.DIRECT,
        requester=requester,
        created_by=user,
        **{**data, "end_date": end_date},
        status=AssetRequestStatus.CONFIRMED,
        handled_by=user,
        assignee=user,
        confirmed_at=timezone.now(),
    )
    _record_created(asset_request, AssetRequestEventKind.DIRECT, user)

    # One line per model, in the order the devices were picked.
    devices = Asset.objects.select_related("model__category").in_bulk(assets)
    stocks = Consumable.objects.select_related("model__category").in_bulk(list(consumables))
    picked: list[tuple[Asset | Consumable, int]] = [
        (devices[pk], 1) for pk in dict.fromkeys(assets) if pk in devices
    ]
    picked += [(stocks[pk], quantity) for pk, quantity in consumables.items() if pk in stocks]
    if len(picked) != len(set(assets)) + len(consumables):
        raise BusinessError(_("A device or consumable was not found."))
    lines: dict[UUID, AssetRequestItem] = {}
    for thing, quantity in picked:
        model = thing.model
        if model.pk not in lines:
            lines[model.pk] = AssetRequestItem(
                asset_request=asset_request,
                position=len(lines),
                category=model.category,
                asset_model=model,
                quantity_requested=0,
            )
        lines[model.pk].quantity_requested += quantity
    for line in lines.values():
        line.quantity_confirmed = line.quantity_requested
        line.save()
    for thing, quantity in picked:
        line = lines[thing.model.pk]
        if isinstance(thing, Asset):
            allocate_asset(line, thing, user)
        else:
            allocate_consumable(line, thing, quantity, user)

    return asset_request


@transaction.atomic
def quick_assign(
    asset: Asset,
    requester: User,
    user: User,
    *,
    duration: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AssetRequest:
    """IT assigns a device from stock to an employee in one step, without request or approval.

    It is recorded as handed out right away, so a temporary assignment keeps its
    return date (reminders, overdue returns) and is taken back like any loan.
    A start date before today records an assignment that began earlier.
    """
    today = timezone.localdate()
    start_date = start_date or today
    if start_date > today:
        raise BusinessError(_("The start date must not be in the future."))
    end_date = end_date if duration == AssetRequest.Duration.TEMPORARY else None
    _validate_period(duration, start_date, end_date)
    if end_date is not None and end_date < today:
        raise BusinessError(_("The return date must not be in the past."))
    asset = Asset.objects.select_for_update().select_related("model__category").get(pk=asset.pk)
    if asset.status != AssetStatus.IN_STOCK:
        raise BusinessError(
            _("%(asset)s is not in stock (%(status)s).")
            % {"asset": asset.inventory_number, "status": asset.get_status_display()}
        )

    now = timezone.now()
    lent = duration == AssetRequest.Duration.TEMPORARY
    asset_request = AssetRequest.objects.create(
        origin=AssetRequest.Origin.QUICK,
        requester=requester,
        created_by=user,
        title=_("Quick assignment"),
        duration=duration,
        start_date=start_date,
        end_date=end_date,
        handover_mode=AssetRequest.HandoverMode.COLLECT,
        status=AssetRequestStatus.HANDED_OUT if lent else AssetRequestStatus.COMPLETED,
        handled_by=user,
        assignee=user,
        confirmed_at=now,
        handed_out_at=now,
        completed_at=None if lent else now,
    )
    _record_created(asset_request, AssetRequestEventKind.QUICK, user)
    item = AssetRequestItem.objects.create(
        asset_request=asset_request,
        category=asset.model.category,
        asset_model=asset.model,
        quantity_requested=1,
        quantity_confirmed=1,
    )
    AssetRequestAllocation.objects.create(item=item, asset=asset, allocated_by=user, handed_out_at=now)
    Handover.objects.create(
        asset_request=asset_request,
        method=HandoverMethod.DIRECT,
        received_by=requester,
        received_by_name=requester.display_name,
        handed_out_by=user,
        recorded_by=user,
    )
    record(
        asset_request,
        AssetRequestEventKind.HANDED_OUT,
        user,
        method=HandoverMethod.DIRECT,
        received_by=requester.display_name,
        items=[asset.inventory_number],
    )
    notifications.request_handed_out(asset_request, [asset.inventory_number], requester.display_name)

    # Begun earlier: the device has been with the employee since that day.
    since = now if start_date == today else timezone.make_aware(datetime.combine(start_date, time.min))
    asset.status = AssetStatus.IN_USE
    asset.assigned_to = requester
    asset.assigned_since = since
    asset.save(update_fields=["status", "assigned_to", "assigned_since", "updated_at"])
    log_event(
        asset,
        AssetEventKind.ASSIGNED,
        user,
        related_user=requester,
        asset_request=asset_request,
        occurred_at=since,
        description=(
            _("Quick assignment until %(date)s")
            % {"date": formats.date_format(end_date, "SHORT_DATE_FORMAT")}
            if end_date is not None
            else _("Quick assignment, permanent")
        ),
    )
    return asset_request


@transaction.atomic
def return_devices(
    asset_request: AssetRequest,
    user: User,
    allocation_ids: list[UUID] | None = None,
    *,
    notes: str = "",
    allocation_notes: dict[UUID, str] | None = None,
    damaged: set[UUID] | None = None,
) -> AssetRequest:
    """Take back lent devices and license seats and document the return.

    Devices listed in ``damaged`` go to repair instead of back into stock. A
    temporary request completes once everything is back; consumables are
    not expected back. Permanently handed-out devices can be taken back as well.
    """
    _require_status(asset_request, *AssetRequest.RETURNABLE_STATUSES)
    allocation_notes = allocation_notes or {}
    damaged = damaged or set()
    now = timezone.now()
    open_allocations = AssetRequestAllocation.objects.filter(
        item__asset_request=asset_request, returned_at__isnull=True, handed_out_at__isnull=False
    ).select_related("asset", "license_assignment")
    returnable = open_allocations.filter(Q(asset__isnull=False) | Q(license__isnull=False))
    selected = list(returnable.filter(pk__in=allocation_ids) if allocation_ids else returnable.all())
    if not selected:
        if (
            asset_request.status == AssetRequestStatus.HANDED_OUT
            and not returnable.exists()
            and not asset_request.devices_unrecorded
        ):
            # Only consumables were handed out: nothing comes back, the request is done.
            open_allocations.update(returned_at=now)
            asset_request.status = AssetRequestStatus.COMPLETED
            asset_request.completed_at = now
            asset_request.save()
            record(asset_request, AssetRequestEventKind.COMPLETED, user)
            return asset_request
        raise BusinessError(_("Nothing is left to take back."))

    taken_back = DeviceReturn.objects.create(
        asset_request=asset_request, notes=notes.strip(), returned_by=user
    )
    for allocation in selected:
        note = allocation_notes.get(allocation.pk, "").strip()
        if allocation.asset:
            asset = allocation.asset
            broken = allocation.pk in damaged
            asset.status = AssetStatus.IN_REPAIR if broken else AssetStatus.IN_STOCK
            asset.assigned_to = None
            asset.assigned_since = None
            asset.save(update_fields=["status", "assigned_to", "assigned_since", "updated_at"])
            log_event(
                asset,
                AssetEventKind.RETURNED,
                user,
                related_user=asset_request.requester,
                asset_request=asset_request,
                description=note,
            )
            if broken:
                log_event(
                    asset,
                    AssetEventKind.STATUS_CHANGED,
                    user,
                    description=_("Returned damaged from %(number)s") % {"number": asset_request.number},
                )
        elif allocation.license_assignment:
            allocation.license_assignment.delete()
            allocation.license_assignment = None
        allocation.returned_at = now
        allocation.device_return = taken_back
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

    taken = [allocation_label(a) for a in selected]
    damaged_labels = [allocation_label(a) for a in selected if a.returned_damaged]
    record(
        asset_request,
        AssetRequestEventKind.RETURNED,
        user,
        items=taken,
        damaged=damaged_labels,
        notes=notes.strip(),
    )
    notifications.request_returned(
        asset_request, taken, damaged_labels, [allocation_label(a) for a in returnable]
    )
    # Devices handed out without being recorded are still out until IT marks them returned.
    if (
        asset_request.status == AssetRequestStatus.HANDED_OUT
        and not returnable.exists()
        and not asset_request.devices_unrecorded
    ):
        open_allocations.update(returned_at=now)
        asset_request.status = AssetRequestStatus.COMPLETED
        asset_request.completed_at = now
        record(asset_request, AssetRequestEventKind.COMPLETED, user)
    asset_request.handled_by = user
    asset_request.save()
    return asset_request


@transaction.atomic
def return_without_devices(asset_request: AssetRequest, user: User, *, notes: str = "") -> AssetRequest:
    """The devices handed out without being recorded are back, still without knowing which.

    Recorded devices still out are taken back on their own; once none are left, the request
    is complete. Devices can no longer be recorded for it.
    """
    _require_status(asset_request, AssetRequestStatus.HANDED_OUT)
    if not asset_request.devices_unrecorded:
        raise BusinessError(_("Every device of this request is recorded. Take them back one by one."))
    now = timezone.now()
    record(
        asset_request,
        AssetRequestEventKind.RETURNED,
        user,
        missing=_missing_labels(asset_request),
        notes=notes.strip(),
    )
    asset_request.devices_unrecorded = False
    asset_request.handled_by = user
    open_allocations = AssetRequestAllocation.objects.filter(
        item__asset_request=asset_request, returned_at__isnull=True, handed_out_at__isnull=False
    )
    if not open_allocations.filter(Q(asset__isnull=False) | Q(license__isnull=False)).exists():
        open_allocations.update(returned_at=now)
        asset_request.status = AssetRequestStatus.COMPLETED
        asset_request.completed_at = now
        record(asset_request, AssetRequestEventKind.COMPLETED, user)
    asset_request.save()
    return asset_request


def release_from_elsewhere(allocation: AssetRequestAllocation, user: User) -> None:
    """A device or seat was taken back outside the request (device or license page).

    Allocations still being prepared must be removed on the request first; lent
    ones count as returned there.
    """
    asset_request = allocation.item.asset_request
    if allocation.handed_out_at is None:
        if asset_request.status in (AssetRequestStatus.CONFIRMED, AssetRequestStatus.READY):
            raise BusinessError(
                _("This is set aside for %(number)s. Remove it there first.")
                % {"number": asset_request.number}
            )
        return
    if allocation.returned_at is None and asset_request.status in AssetRequest.RETURNABLE_STATUSES:
        return_devices(asset_request, user, [allocation.pk])

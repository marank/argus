"""Purchase order life cycle: draft → ordered → (partially) received."""

import calendar
from datetime import date

from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, ConsumableMovement
from apps.inventory.services import assets as asset_service
from apps.inventory.services.consumables import get_consumable, move_consumable
from apps.procurement.models import PurchaseOrder, PurchaseOrderLine
from apps.requests.models import AssetRequest
from apps.requests.services import workflow

Status = PurchaseOrder.Status


def _require_status(order: PurchaseOrder, *allowed: str) -> None:
    if order.status not in allowed:
        raise BusinessError(
            _("This is not possible while the order is “%(status)s”.")
            % {"status": order.get_status_display()}
        )


def _save_lines(order: PurchaseOrder, lines: list[dict]) -> None:
    if not lines:
        raise BusinessError(_("An order needs at least one line."))
    keep = []
    for position, data in enumerate(lines):
        line_id = data.get("id")
        line = order.lines.filter(pk=line_id).first() if line_id else None
        line = line or PurchaseOrderLine(order=order)
        line.asset_model_id = data.get("asset_model")
        line.description = data.get("description", "")
        line.quantity = data["quantity"]
        line.unit_price = data.get("unit_price")
        if line.unit_price is None and line.asset_model is not None:
            line.unit_price = line.asset_model.list_price
        line.asset_request_item_id = data.get("asset_request_item")
        line.position = position
        line.full_clean()
        line.save()
        keep.append(line.pk)
    order.lines.exclude(pk__in=keep).delete()


@transaction.atomic
def create_order(data: dict, lines: list[dict], user) -> PurchaseOrder:
    order = PurchaseOrder(created_by=user)
    _apply(order, data)
    order.save()
    _save_lines(order, lines)
    return order


@transaction.atomic
def update_order(order: PurchaseOrder, data: dict, lines: list[dict] | None) -> PurchaseOrder:
    if lines is not None:
        _require_status(order, Status.DRAFT)
    _apply(order, data)
    order.save()
    if lines is not None:
        _save_lines(order, lines)
    return order


def _apply(order: PurchaseOrder, data: dict) -> None:
    for name, value in data.items():
        field = order._meta.get_field(name)
        setattr(order, f"{name}_id" if field.is_relation else name, value)
    # The number is drawn when saving.
    order.full_clean(exclude=["number"])


@transaction.atomic
def mark_ordered(
    order: PurchaseOrder, order_date: date | None, expected_date: date | None, reference: str
) -> PurchaseOrder:
    _require_status(order, Status.DRAFT)
    order.status = Status.ORDERED
    order.order_date = order_date or timezone.localdate()
    order.expected_date = expected_date
    order.supplier_reference = reference
    order.save()
    return order


@transaction.atomic
def cancel(order: PurchaseOrder) -> PurchaseOrder:
    _require_status(order, Status.DRAFT, Status.ORDERED)
    order.status = Status.CANCELLED
    order.save()
    return order


def _add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


@transaction.atomic
def receive(order: PurchaseOrder, receipts: list[dict], user) -> PurchaseOrder:
    """Book a delivery: creates devices or increases consumable quantities.

    Devices that were ordered for a request are allocated to it right away
    while the request is still being prepared.
    """
    # Locked and read again: two deliveries booked at once must not both see the
    # same open quantity.
    order = PurchaseOrder.objects.select_for_update().get(pk=order.pk)
    _require_status(order, Status.ORDERED, Status.PARTIALLY_RECEIVED)
    today = timezone.localdate()
    order_lines = {
        line.pk: line
        for line in order.lines.select_for_update(of=("self",)).select_related(
            "asset_model", "asset_request_item__asset_request"
        )
    }

    for receipt in receipts:
        line = order_lines.get(receipt["line"])
        if line is None:
            raise Http404
        model = line.asset_model
        if model is None:
            raise BusinessError(_("Assign a model to “%(line)s” before receiving it.") % {"line": line.label})
        location_id = receipt.get("location") or order.delivery_location_id
        serials = [s.strip() for s in receipt.get("serial_numbers", []) if s.strip()]
        quantity = len(serials) if not model.is_bulk and serials else receipt["quantity"]
        if quantity < 1:
            continue
        if quantity > line.quantity_open:
            raise BusinessError(
                _("Only %(open)s units of “%(line)s” are still open.")
                % {"open": line.quantity_open, "line": line.label}
            )

        item = line.asset_request_item
        if item is not None and item.asset_request.status != AssetRequest.Status.CONFIRMED:
            item = None  # only confirmed requests get the delivered units

        if model.is_bulk:
            if not location_id:
                raise BusinessError(_("Choose a storage location for consumables."))
            consumable = get_consumable(model.pk, location_id)
            move_consumable(
                consumable,
                quantity,
                ConsumableMovement.Reason.RECEIPT,
                user,
                purchase_order_line=line,
                note=order.number,
            )
            if item is not None:
                take = min(quantity, item.quantity_missing)
                if take:
                    workflow.allocate_consumable(item, consumable, take, user)
        elif model.is_software:
            pass  # Seats are recorded as a license under Licenses, not as devices.
        else:
            serials = serials or [""] * quantity
            for serial in serials:
                asset = asset_service.create_asset(
                    {
                        "model": model.pk,
                        "serial_number": serial,
                        "status": Asset.Status.IN_STOCK,
                        "location": location_id,
                        "supplier": order.supplier_id,
                        "purchase_order_line": line.pk,
                        "purchase_date": today,
                        "purchase_price": line.unit_price,
                        "warranty_until": _add_months(today, model.warranty_months),
                    },
                    user,
                )
                if item is not None and item.quantity_missing:
                    workflow.allocate_asset(item, asset, user)

        line.quantity_received += quantity
        line.save(update_fields=["quantity_received"])

    lines = list(order.lines.all())
    if all(line.quantity_open == 0 for line in lines):
        order.status = Status.RECEIVED
    elif any(line.quantity_received for line in lines):
        order.status = Status.PARTIALLY_RECEIVED
    order.save()
    return order

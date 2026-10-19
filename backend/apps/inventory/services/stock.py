from uuid import UUID

from django.db import transaction
from django.utils.translation import gettext as _

from apps.core.exceptions import BusinessError
from apps.inventory.models import StockItem, StockMovement


def get_stock_item(model_id: UUID, location_id: UUID) -> StockItem:
    item, _ = StockItem.objects.get_or_create(model_id=model_id, location_id=location_id)
    return item


@transaction.atomic
def move_stock(
    stock_item: StockItem,
    delta: int,
    reason: str,
    user=None,
    *,
    release_reserved: int = 0,
    **fields,
) -> StockMovement:
    """Change the quantity of a stock item and record the movement.

    ``release_reserved`` lowers the reserved quantity in the same step, used when
    reserved goods are handed out.
    """
    item = StockItem.objects.select_for_update().get(pk=stock_item.pk)
    if item.quantity + delta < 0:
        raise BusinessError(
            _("Not enough stock for %(model)s (available: %(quantity)s).")
            % {"model": item.model, "quantity": item.quantity}
        )
    item.quantity += delta
    item.reserved_quantity = max(item.reserved_quantity - release_reserved, 0)
    item.save(update_fields=["quantity", "reserved_quantity", "updated_at"])
    return StockMovement.objects.create(
        stock_item=item, delta=delta, reason=reason, performed_by=user, **fields
    )


@transaction.atomic
def reserve_stock(stock_item: StockItem, quantity: int) -> None:
    item = StockItem.objects.select_for_update().get(pk=stock_item.pk)
    if item.available_quantity < quantity:
        raise BusinessError(
            _("Only %(available)s units of %(model)s are available at %(location)s.")
            % {"available": item.available_quantity, "model": item.model, "location": item.location}
        )
    item.reserved_quantity += quantity
    item.save(update_fields=["reserved_quantity", "updated_at"])


@transaction.atomic
def release_stock(stock_item: StockItem, quantity: int) -> None:
    item = StockItem.objects.select_for_update().get(pk=stock_item.pk)
    item.reserved_quantity = max(item.reserved_quantity - quantity, 0)
    item.save(update_fields=["reserved_quantity", "updated_at"])

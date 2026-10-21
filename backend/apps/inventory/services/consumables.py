from uuid import UUID

from django.db import transaction
from django.utils.translation import gettext as _

from apps.core.exceptions import BusinessError
from apps.inventory.models import Consumable, ConsumableMovement


def get_consumable(model_id: UUID, location_id: UUID) -> Consumable:
    item, _ = Consumable.objects.get_or_create(model_id=model_id, location_id=location_id)
    return item


@transaction.atomic
def move_consumable(
    consumable: Consumable,
    delta: int,
    reason: str,
    user=None,
    *,
    release_reserved: int = 0,
    **fields,
) -> ConsumableMovement:
    """Change the quantity of a consumable and record the movement.

    ``release_reserved`` lowers the reserved quantity in the same step, used when
    reserved goods are handed out.
    """
    item = Consumable.objects.select_for_update().get(pk=consumable.pk)
    item.reserved_quantity = max(item.reserved_quantity - release_reserved, 0)
    # Units reserved for open requests are spoken for: only the rest may be booked out.
    if delta < 0 and -delta > item.available_quantity:
        if item.reserved_quantity:
            raise BusinessError(
                _(
                    "Not enough stock for %(model)s: only %(available)s available, "
                    "%(reserved)s are reserved for requests."
                )
                % {
                    "model": item.model,
                    "available": item.available_quantity,
                    "reserved": item.reserved_quantity,
                }
            )
        raise BusinessError(
            _("Not enough stock for %(model)s (available: %(quantity)s).")
            % {"model": item.model, "quantity": item.quantity}
        )
    item.quantity += delta
    item.save(update_fields=["quantity", "reserved_quantity", "updated_at"])
    return ConsumableMovement.objects.create(
        consumable=item, delta=delta, reason=reason, performed_by=user, **fields
    )


@transaction.atomic
def reserve_consumable(consumable: Consumable, quantity: int) -> None:
    item = Consumable.objects.select_for_update().get(pk=consumable.pk)
    if item.available_quantity < quantity:
        raise BusinessError(
            _("Only %(available)s units of %(model)s are available at %(location)s.")
            % {"available": item.available_quantity, "model": item.model, "location": item.location}
        )
    item.reserved_quantity += quantity
    item.save(update_fields=["reserved_quantity", "updated_at"])


@transaction.atomic
def release_consumable(consumable: Consumable, quantity: int) -> None:
    item = Consumable.objects.select_for_update().get(pk=consumable.pk)
    item.reserved_quantity = max(item.reserved_quantity - quantity, 0)
    item.save(update_fields=["reserved_quantity", "updated_at"])

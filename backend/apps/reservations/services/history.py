"""The history of a request, written by the workflow as each step happens."""

from apps.reservations.models import Reservation, ReservationAllocation, ReservationEvent

Kind = ReservationEvent.Kind


def record(reservation: Reservation, kind: str, user=None, **data) -> ReservationEvent:
    """Note a step; ``data`` holds plain values (texts, dates as ISO strings)."""
    return ReservationEvent.objects.create(
        reservation=reservation,
        kind=kind,
        actor=user if getattr(user, "pk", None) else None,
        data={key: value for key, value in data.items() if value not in (None, "", [])},
    )


def allocation_label(allocation: ReservationAllocation) -> str:
    """What was allocated, readable on its own: "MDE-0001", "2× USB-C cable", "Seat: Office"."""
    if allocation.asset_id:
        return allocation.asset.inventory_number
    if allocation.consumable_id:
        return f"{allocation.quantity}× {allocation.consumable.model}"
    return str(allocation.license.model)

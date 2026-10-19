from django.db import transaction

from apps.core.models import NumberSequence

DEFAULT_SEQUENCES = {
    "asset": {"name": "Assets", "prefix": "INV-", "pattern": "{prefix}{seq}", "padding": 6},
    "reservation": {
        "name": "Reservations",
        "prefix": "RES-",
        "pattern": "{prefix}{year}-{seq}",
        "padding": 5,
        "reset_period": NumberSequence.ResetPeriod.YEARLY,
    },
    "purchase-order": {
        "name": "Purchase orders",
        "prefix": "PO-",
        "pattern": "{prefix}{year}-{seq}",
        "padding": 4,
        "reset_period": NumberSequence.ResetPeriod.YEARLY,
    },
}


def get_sequence(code: str) -> NumberSequence:
    """Return the sequence with ``code``, creating a sensible default if missing."""
    sequence, _ = NumberSequence.objects.get_or_create(
        code=code, defaults=DEFAULT_SEQUENCES.get(code, {"name": code})
    )
    return sequence


def next_number(sequence: NumberSequence | str) -> str:
    """Atomically draw the next number from a sequence."""
    if isinstance(sequence, str):
        sequence = get_sequence(sequence)

    with transaction.atomic():
        locked = NumberSequence.objects.select_for_update().get(pk=sequence.pk)
        period = locked.current_period_key()
        if locked.period_key != period:
            locked.period_key = period
            locked.next_value = 1
        value = locked.next_value
        locked.next_value += 1
        locked.save(update_fields=["next_value", "period_key", "updated_at"])
    return locked.format(value)

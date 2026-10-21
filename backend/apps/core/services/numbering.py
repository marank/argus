from collections.abc import Callable

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
    """Return the sequence with ``code``, creating a sensible default if missing.

    The system sequences come with a migration; this only recreates one removed from the database.
    """
    defaults = {**DEFAULT_SEQUENCES[code], "is_system": True} if code in DEFAULT_SEQUENCES else {"name": code}
    sequence, _ = NumberSequence.objects.get_or_create(code=code, defaults=defaults)
    return sequence


def next_number(sequence: NumberSequence | str, taken: Callable[[str], bool] | None = None) -> str:
    """Atomically draw the next number from a sequence.

    Numbers for which ``taken`` returns true are skipped: one may already exist after the
    format or the next value was changed, or after a number was entered by hand.
    """
    if isinstance(sequence, str):
        sequence = get_sequence(sequence)

    with transaction.atomic():
        locked = NumberSequence.objects.select_for_update().get(pk=sequence.pk)
        period = locked.current_period_key()
        if locked.period_key != period:
            locked.period_key = period
            locked.next_value = 1
        while True:
            number = locked.format(locked.next_value)
            locked.next_value += 1
            if not (taken and taken(number)):
                break
        locked.save(update_fields=["next_value", "period_key", "updated_at"])
    return number

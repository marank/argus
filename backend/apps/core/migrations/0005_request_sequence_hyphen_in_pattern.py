from django.db import migrations

# code: (old name, new name), (old prefix, old pattern), (new prefix, new pattern)
CHANGES = {
    "asset": (("Assets", "Assets"), ("INV-", "{prefix}{seq}"), ("INV", "{prefix}-{seq}")),
    "request": (
        ("Reservations", "Requests"),
        ("RES-", "{prefix}{year}-{seq}"),
        ("RES", "{prefix}-{year}-{seq}"),
    ),
    "purchase-order": (
        ("Purchase orders", "Purchase orders"),
        ("PO-", "{prefix}{year}-{seq}"),
        ("PO", "{prefix}-{year}-{seq}"),
    ),
}


def _rename_code(NumberSequence, old: str, new: str) -> None:
    # Reservations are requests now; the numbers keep counting in the same sequence.
    if not NumberSequence.objects.filter(code=new).exists():
        NumberSequence.objects.filter(code=old).update(code=new)


def _apply(NumberSequence, forward: bool) -> None:
    """Moves the hyphen from the prefix into the pattern; the numbers come out the same.

    Only sequences still in their original format: a changed name, prefix or pattern stays.
    """
    for code, (names, old, new) in CHANGES.items():
        if not forward:
            names, old, new = names[::-1], new, old
        sequence = NumberSequence.objects.filter(code=code).first()
        if sequence is None:
            continue
        if sequence.name == names[0]:
            sequence.name = names[1]
        if (sequence.prefix, sequence.pattern) == old:
            sequence.prefix, sequence.pattern = new
        sequence.save(update_fields=["name", "prefix", "pattern"])


def forward(apps, schema_editor):
    NumberSequence = apps.get_model("core", "NumberSequence")
    _rename_code(NumberSequence, "reservation", "request")
    _apply(NumberSequence, forward=True)


def backward(apps, schema_editor):
    NumberSequence = apps.get_model("core", "NumberSequence")
    _apply(NumberSequence, forward=False)
    _rename_code(NumberSequence, "request", "reservation")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_system_number_sequences"),
    ]

    operations = [migrations.RunPython(forward, backward)]

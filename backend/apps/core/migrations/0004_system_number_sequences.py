from django.db import migrations, models

# The sequences Argus draws from by code, with their formats at the time of this migration.
SYSTEM_SEQUENCES = {
    "asset": {"name": "Assets", "prefix": "INV-", "pattern": "{prefix}{seq}", "padding": 6},
    "reservation": {
        "name": "Reservations",
        "prefix": "RES-",
        "pattern": "{prefix}{year}-{seq}",
        "padding": 5,
        "reset_period": "yearly",
    },
    "purchase-order": {
        "name": "Purchase orders",
        "prefix": "PO-",
        "pattern": "{prefix}{year}-{seq}",
        "padding": 4,
        "reset_period": "yearly",
    },
}


def create_system_sequences(apps, schema_editor):
    """Creates the system sequences up front, so they can be set up before the first number;
    existing ones keep their format and only get marked."""
    NumberSequence = apps.get_model("core", "NumberSequence")
    for code, defaults in SYSTEM_SEQUENCES.items():
        sequence, _ = NumberSequence.objects.get_or_create(code=code, defaults=defaults)
        sequence.is_system = True
        sequence.save(update_fields=["is_system"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_notifications_and_rules"),
    ]

    operations = [
        migrations.AddField(
            model_name="numbersequence",
            name="is_system",
            field=models.BooleanField(default=False, editable=False, verbose_name="system sequence"),
        ),
        migrations.AlterField(
            model_name="numbersequence",
            name="code",
            field=models.SlugField(blank=True, verbose_name="code"),
        ),
        migrations.AddConstraint(
            model_name="numbersequence",
            constraint=models.UniqueConstraint(
                condition=models.Q(("code", ""), _negated=True),
                fields=("code",),
                name="unique_number_sequence_code",
                violation_error_code="unique",
                violation_error_message="A number sequence with this code already exists.",
            ),
        ),
        migrations.RunPython(create_system_sequences, migrations.RunPython.noop),
    ]

import django.db.models.deletion
from django.db import migrations, models
from django.db.models.functions import Lower


def refuse_duplicate_names(apps, schema_editor):
    """Two devices in use with the same hostname would break the new constraint; say which."""
    Asset = apps.get_model("inventory", "Asset")
    duplicates = (
        Asset.objects.exclude(name="")
        .exclude(status__in=["lost", "retired"])
        .values("name")
        .annotate(count=models.Count("pk"))
        .filter(count__gt=1)
        .order_by(Lower("name"))
    )
    names = [row["name"] for row in duplicates]
    if names:
        raise RuntimeError(
            "Several devices in use have the same hostname; rename or clear them first: " + ", ".join(names)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0006_mac_address_with_colons"),
    ]

    operations = [
        migrations.RenameField(model_name="asset", old_name="hostname", new_name="name"),
        migrations.AlterField(
            model_name="asset",
            name="name",
            field=models.CharField(
                blank=True,
                help_text="What the device is called in daily use, e.g. its hostname or its name in the MDM.",
                max_length=100,
                verbose_name="device name",
            ),
        ),
        migrations.AddField(
            model_name="assetevent",
            name="related_asset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="inventory.asset",
                verbose_name="related device",
            ),
        ),
        migrations.AlterField(
            model_name="assetevent",
            name="kind",
            field=models.CharField(
                choices=[
                    ("created", "Created"),
                    ("status_changed", "Status changed"),
                    ("assigned", "Handed out"),
                    ("returned", "Returned"),
                    ("reserved", "Reserved"),
                    ("replaced", "Device replaced"),
                    ("component_replaced", "Component replaced"),
                    ("repair", "Repair"),
                    ("maintenance", "Maintenance"),
                    ("inspection", "Inspection"),
                    ("note", "Note"),
                    ("issue_reported", "Problem reported"),
                    ("issue_resolved", "Problem resolved"),
                ],
                db_index=True,
                max_length=20,
                verbose_name="kind",
            ),
        ),
        migrations.RunPython(refuse_duplicate_names, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="asset",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    models.Q(("name", ""), _negated=True),
                    models.Q(("status__in", ["lost", "retired"]), _negated=True),
                ),
                fields=("name",),
                name="unique_active_device_name",
                violation_error_code="unique",
                violation_error_message="Another device in use already has this name.",
            ),
        ),
    ]

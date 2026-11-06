import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0003_uuid7_ids"),
        ("masterdata", "0009_category_identifier_label_componenttype"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="identifier",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="A further number of the manufacturer, e.g. the configuration of the device (Handtec CN, Lenovo MTM). The category says what it is called there.",
                max_length=100,
                verbose_name="identifier",
            ),
        ),
        migrations.AddField(
            model_name="assetevent",
            name="component_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="masterdata.componenttype",
                verbose_name="component type",
            ),
        ),
        migrations.AddField(
            model_name="assetevent",
            name="previous_serial",
            field=models.CharField(blank=True, max_length=100, verbose_name="previous serial number"),
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
        migrations.CreateModel(
            name="AssetComponent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                (
                    "serial_number",
                    models.CharField(blank=True, db_index=True, max_length=100, verbose_name="serial number"),
                ),
                ("installed_on", models.DateField(blank=True, null=True, verbose_name="installed on")),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="installed_components",
                        to="inventory.asset",
                        verbose_name="asset",
                    ),
                ),
                (
                    "component_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="installed",
                        to="masterdata.componenttype",
                        verbose_name="component type",
                    ),
                ),
            ],
            options={
                "verbose_name": "installed component",
                "verbose_name_plural": "installed components",
                "ordering": ["component_type__sort_order", "component_type__name"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("asset", "component_type"), name="unique_asset_component_type"
                    )
                ],
            },
        ),
    ]

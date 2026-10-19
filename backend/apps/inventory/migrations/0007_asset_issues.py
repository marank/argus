import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0006_licenses"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
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
                    ("battery_replaced", "Battery replaced"),
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
            name="AssetIssue",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("defect", "Not working"),
                            ("damage", "Damaged"),
                            ("lost", "Lost or stolen"),
                            ("other", "Other"),
                        ],
                        default="defect",
                        max_length=10,
                        verbose_name="kind",
                    ),
                ),
                ("description", models.TextField(verbose_name="description")),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("in_progress", "In progress"), ("resolved", "Resolved")],
                        db_index=True,
                        default="open",
                        max_length=12,
                        verbose_name="status",
                    ),
                ),
                ("resolution", models.TextField(blank=True, verbose_name="resolution")),
                ("resolved_at", models.DateTimeField(blank=True, null=True, verbose_name="resolved at")),
                (
                    "asset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="issues",
                        to="inventory.asset",
                        verbose_name="device",
                    ),
                ),
                (
                    "handled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="handled by",
                    ),
                ),
                (
                    "reported_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reported_issues",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="reported by",
                    ),
                ),
            ],
            options={
                "verbose_name": "problem report",
                "verbose_name_plural": "problem reports",
                "ordering": ["-created_at"],
            },
        ),
    ]

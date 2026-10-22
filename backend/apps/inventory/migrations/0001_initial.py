import uuid

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("masterdata", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetEvent",
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
                (
                    "occurred_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="occurred at"),
                ),
                ("description", models.TextField(blank=True, verbose_name="description")),
                ("component", models.CharField(blank=True, max_length=100, verbose_name="component")),
                (
                    "component_serial",
                    models.CharField(blank=True, max_length=100, verbose_name="component serial number"),
                ),
                (
                    "cost",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="cost"
                    ),
                ),
            ],
            options={
                "verbose_name": "asset event",
                "verbose_name_plural": "asset events",
                "ordering": ["-occurred_at", "-created_at"],
            },
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
                ("resolved_at", models.DateTimeField(blank=True, null=True, verbose_name="resolved at")),
                ("unseen_update", models.BooleanField(default=False, verbose_name="unseen update")),
            ],
            options={
                "verbose_name": "problem report",
                "verbose_name_plural": "problem reports",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AssetIssueEntry",
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
                        choices=[("message", "Message"), ("status", "Change of status")],
                        max_length=10,
                        verbose_name="kind",
                    ),
                ),
                ("text", models.TextField(blank=True, verbose_name="text")),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[("open", "Open"), ("in_progress", "In progress"), ("resolved", "Resolved")],
                        max_length=12,
                        verbose_name="status",
                    ),
                ),
            ],
            options={
                "verbose_name": "problem report entry",
                "verbose_name_plural": "problem report entries",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="Consumable",
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
                ("quantity", models.IntegerField(default=0, verbose_name="quantity")),
                (
                    "reserved_quantity",
                    models.PositiveIntegerField(default=0, verbose_name="reserved quantity"),
                ),
                (
                    "min_quantity",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Reorder when the stock falls below.",
                        verbose_name="minimum quantity",
                    ),
                ),
            ],
            options={
                "verbose_name": "consumable",
                "verbose_name_plural": "consumables",
                "ordering": ["model__name"],
            },
        ),
        migrations.CreateModel(
            name="ConsumableMovement",
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
                ("delta", models.IntegerField(verbose_name="change")),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("receipt", "Goods receipt"),
                            ("issue", "Issue"),
                            ("return", "Return"),
                            ("adjustment", "Adjustment"),
                            ("consumption", "Used for repair"),
                        ],
                        max_length=12,
                        verbose_name="reason",
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=255, verbose_name="note")),
            ],
            options={
                "verbose_name": "consumable movement",
                "verbose_name_plural": "consumable movements",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="License",
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
                    "reference",
                    models.CharField(
                        blank=True,
                        help_text="E.g. contract number or agreement, to tell several licenses apart.",
                        max_length=150,
                        verbose_name="contract / reference",
                    ),
                ),
                ("license_key", models.CharField(blank=True, max_length=255, verbose_name="license key")),
                (
                    "seats",
                    models.PositiveIntegerField(
                        default=1,
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="seats",
                    ),
                ),
                (
                    "assign_to",
                    models.CharField(
                        choices=[("user", "Employees"), ("device", "Devices")],
                        default="user",
                        max_length=10,
                        verbose_name="assigned to",
                    ),
                ),
                ("valid_from", models.DateField(blank=True, null=True, verbose_name="valid from")),
                (
                    "valid_until",
                    models.DateField(
                        blank=True,
                        help_text="Leave empty for perpetual licenses.",
                        null=True,
                        verbose_name="valid until",
                    ),
                ),
                ("purchase_date", models.DateField(blank=True, null=True, verbose_name="purchase date")),
                (
                    "purchase_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="purchase price"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
            ],
            options={
                "verbose_name": "license",
                "verbose_name_plural": "licenses",
                "ordering": ["model__name", "valid_until", "created_at"],
            },
        ),
        migrations.CreateModel(
            name="LicenseAssignment",
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
                ("note", models.CharField(blank=True, max_length=255, verbose_name="note")),
            ],
            options={
                "verbose_name": "license assignment",
                "verbose_name_plural": "license assignments",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="Asset",
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
                    "inventory_number",
                    models.CharField(blank=True, max_length=50, unique=True, verbose_name="inventory number"),
                ),
                (
                    "serial_number",
                    models.CharField(blank=True, db_index=True, max_length=100, verbose_name="serial number"),
                ),
                ("imei", models.CharField(blank=True, max_length=20, verbose_name="IMEI")),
                ("mac_address", models.CharField(blank=True, max_length=17, verbose_name="MAC address")),
                ("hostname", models.CharField(blank=True, max_length=63, verbose_name="hostname")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("in_stock", "In stock"),
                            ("reserved", "Reserved"),
                            ("in_use", "In use"),
                            ("in_repair", "In repair"),
                            ("lost", "Lost"),
                            ("retired", "Retired"),
                        ],
                        db_index=True,
                        default="in_stock",
                        max_length=12,
                        verbose_name="status",
                    ),
                ),
                (
                    "condition",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("good", "Good"),
                            ("worn", "Worn"),
                            ("defective", "Defective"),
                        ],
                        default="new",
                        max_length=10,
                        verbose_name="condition",
                    ),
                ),
                (
                    "is_loanable",
                    models.BooleanField(
                        default=True,
                        help_text="Part of the pool employees can reserve from.",
                        verbose_name="loanable",
                    ),
                ),
                (
                    "assigned_since",
                    models.DateTimeField(blank=True, null=True, verbose_name="assigned since"),
                ),
                ("purchase_date", models.DateField(blank=True, null=True, verbose_name="purchase date")),
                (
                    "purchase_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="purchase price"
                    ),
                ),
                ("warranty_until", models.DateField(blank=True, null=True, verbose_name="warranty until")),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assets",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="assigned to",
                    ),
                ),
                (
                    "consumables",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Consumables for this device in addition to those compatible with its model.",
                        limit_choices_to={"tracking": "bulk"},
                        related_name="consuming_assets",
                        to="masterdata.assetmodel",
                        verbose_name="consumables",
                    ),
                ),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assets",
                        to="masterdata.location",
                        verbose_name="location",
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assets",
                        to="masterdata.assetmodel",
                        verbose_name="model",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        help_text="E.g. a docking station or handle that belongs to another device.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="components",
                        to="inventory.asset",
                        verbose_name="belongs to",
                    ),
                ),
            ],
            options={
                "verbose_name": "asset",
                "verbose_name_plural": "assets",
                "ordering": ["inventory_number"],
            },
        ),
    ]

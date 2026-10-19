import uuid

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
                "ordering": ["-occurred_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="StockItem",
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
                "verbose_name": "stock item",
                "verbose_name_plural": "stock items",
                "ordering": ["model__name"],
            },
        ),
        migrations.CreateModel(
            name="StockMovement",
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
                "verbose_name": "stock movement",
                "verbose_name_plural": "stock movements",
                "ordering": ["-created_at", "-id"],
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

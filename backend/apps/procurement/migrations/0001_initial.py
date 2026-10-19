import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("masterdata", "0001_initial"),
        ("reservations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PurchaseOrder",
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
                ("number", models.CharField(blank=True, max_length=30, unique=True, verbose_name="number")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "To order"),
                            ("ordered", "Ordered"),
                            ("partially_received", "Partially received"),
                            ("received", "Received"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                ("order_date", models.DateField(blank=True, null=True, verbose_name="order date")),
                ("expected_date", models.DateField(blank=True, null=True, verbose_name="expected delivery")),
                (
                    "supplier_reference",
                    models.CharField(blank=True, max_length=100, verbose_name="supplier reference"),
                ),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "delivery_location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="masterdata.location",
                        verbose_name="delivery location",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="purchase_orders",
                        to="masterdata.supplier",
                        verbose_name="supplier",
                    ),
                ),
            ],
            options={
                "verbose_name": "purchase order",
                "verbose_name_plural": "purchase orders",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PurchaseOrderLine",
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
                ("description", models.CharField(blank=True, max_length=255, verbose_name="description")),
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="quantity")),
                (
                    "unit_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="unit price"
                    ),
                ),
                (
                    "quantity_received",
                    models.PositiveIntegerField(default=0, verbose_name="received quantity"),
                ),
                (
                    "asset_model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_lines",
                        to="masterdata.assetmodel",
                        verbose_name="model",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lines",
                        to="procurement.purchaseorder",
                        verbose_name="purchase order",
                    ),
                ),
                (
                    "reservation_item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="order_lines",
                        to="reservations.reservationitem",
                        verbose_name="for reservation item",
                    ),
                ),
            ],
            options={
                "verbose_name": "order line",
                "verbose_name_plural": "order lines",
                "ordering": ["id"],
            },
        ),
    ]

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("inventory", "0001_initial"),
        ("masterdata", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Reservation",
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
                ("title", models.CharField(max_length=200, verbose_name="purpose")),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                (
                    "duration",
                    models.CharField(
                        choices=[("temporary", "Temporary"), ("permanent", "Permanent")],
                        default="temporary",
                        max_length=10,
                        verbose_name="duration",
                    ),
                ),
                ("start_date", models.DateField(verbose_name="needed from")),
                ("end_date", models.DateField(blank=True, null=True, verbose_name="needed until")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("submitted", "Submitted"),
                            ("approved", "Approved"),
                            ("ready", "Ready for pickup"),
                            ("handed_out", "Handed out"),
                            ("completed", "Completed"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="submitted",
                        max_length=12,
                        verbose_name="status",
                    ),
                ),
                ("pickup_at", models.DateTimeField(blank=True, null=True, verbose_name="pickup at")),
                (
                    "handover_mode",
                    models.CharField(
                        choices=[("pickup", "Pickup with signature"), ("delivery", "Delivered by IT")],
                        default="pickup",
                        help_text="Pickup requests appear on the pickup terminal once they are ready.",
                        max_length=10,
                        verbose_name="handover",
                    ),
                ),
                ("it_comment", models.TextField(blank=True, verbose_name="IT comment")),
                ("approved_at", models.DateTimeField(blank=True, null=True, verbose_name="approved at")),
                ("handed_out_at", models.DateTimeField(blank=True, null=True, verbose_name="handed out at")),
                ("completed_at", models.DateTimeField(blank=True, null=True, verbose_name="completed at")),
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
                    "handled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="handled_reservations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="handled by",
                    ),
                ),
                (
                    "pickup_location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="masterdata.location",
                        verbose_name="pickup location",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="requester",
                    ),
                ),
            ],
            options={
                "verbose_name": "reservation",
                "verbose_name_plural": "reservations",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Handover",
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
                (
                    "method",
                    models.CharField(
                        choices=[
                            ("signature", "Signed at pickup terminal"),
                            ("delivered", "Delivered by IT"),
                            ("direct", "Handed out by IT"),
                        ],
                        max_length=10,
                        verbose_name="method",
                    ),
                ),
                (
                    "received_by_name",
                    models.CharField(
                        help_text="Kept as text so the record stays readable if the account is removed.",
                        max_length=150,
                        verbose_name="received by (name)",
                    ),
                ),
                (
                    "signature",
                    models.TextField(
                        blank=True, help_text="PNG image as data URL.", verbose_name="signature"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                ("location", models.CharField(blank=True, max_length=150, verbose_name="delivered to")),
                ("handed_out_at", models.DateTimeField(auto_now_add=True, verbose_name="handed out at")),
                (
                    "handed_out_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="handed out by",
                    ),
                ),
                (
                    "received_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="received_handovers",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="received by",
                    ),
                ),
                (
                    "reservation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="handover",
                        to="reservations.reservation",
                        verbose_name="reservation",
                    ),
                ),
            ],
            options={
                "verbose_name": "handover",
                "verbose_name_plural": "handovers",
            },
        ),
        migrations.CreateModel(
            name="ReservationItem",
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
                (
                    "quantity_requested",
                    models.PositiveIntegerField(default=1, verbose_name="requested quantity"),
                ),
                (
                    "quantity_approved",
                    models.PositiveIntegerField(blank=True, null=True, verbose_name="approved quantity"),
                ),
                ("note", models.CharField(blank=True, max_length=255, verbose_name="note")),
                (
                    "asset_model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="masterdata.assetmodel",
                        verbose_name="model",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="masterdata.category",
                        verbose_name="category",
                    ),
                ),
                (
                    "reservation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="reservations.reservation",
                        verbose_name="reservation",
                    ),
                ),
            ],
            options={
                "verbose_name": "reservation item",
                "verbose_name_plural": "reservation items",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="ReservationAllocation",
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
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="quantity")),
                ("allocated_at", models.DateTimeField(auto_now_add=True, verbose_name="allocated at")),
                (
                    "handout_note",
                    models.CharField(
                        blank=True,
                        help_text="E.g. a scratch on the lid.",
                        max_length=255,
                        verbose_name="hand-out note",
                    ),
                ),
                ("handed_out_at", models.DateTimeField(blank=True, null=True, verbose_name="handed out at")),
                ("returned_at", models.DateTimeField(blank=True, null=True, verbose_name="returned at")),
                (
                    "allocated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="allocated by",
                    ),
                ),
                (
                    "asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservation_allocations",
                        to="inventory.asset",
                        verbose_name="asset",
                    ),
                ),
                (
                    "stock_item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservation_allocations",
                        to="inventory.stockitem",
                        verbose_name="stock item",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allocations",
                        to="reservations.reservationitem",
                        verbose_name="reservation item",
                    ),
                ),
            ],
            options={
                "verbose_name": "allocation",
                "verbose_name_plural": "allocations",
                "ordering": ["id"],
            },
        ),
    ]

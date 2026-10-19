import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0005_consumable_fields_asset_consumables"),
        ("masterdata", "0004_category_kind_license_tracking"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
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
                (
                    "model",
                    models.ForeignKey(
                        limit_choices_to={"tracking": "license"},
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="licenses",
                        to="masterdata.assetmodel",
                        verbose_name="software",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="licenses",
                        to="masterdata.supplier",
                        verbose_name="supplier",
                    ),
                ),
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
                (
                    "asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="license_assignments",
                        to="inventory.asset",
                        verbose_name="device",
                    ),
                ),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="assigned by",
                    ),
                ),
                (
                    "license",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="inventory.license",
                        verbose_name="license",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="license_assignments",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="employee",
                    ),
                ),
            ],
            options={
                "verbose_name": "license assignment",
                "verbose_name_plural": "license assignments",
                "ordering": ["created_at"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(("asset__isnull", True), ("user__isnull", False)),
                            models.Q(("asset__isnull", False), ("user__isnull", True)),
                            _connector="OR",
                        ),
                        name="license_assignment_user_or_asset",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("user__isnull", False)),
                        fields=("license", "user"),
                        name="unique_license_user",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("asset__isnull", False)),
                        fields=("license", "asset"),
                        name="unique_license_asset",
                    ),
                ],
            },
        ),
    ]

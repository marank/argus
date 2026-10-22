import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Manufacturer",
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
                ("name", models.CharField(max_length=100, unique=True, verbose_name="name")),
                ("website", models.URLField(blank=True, verbose_name="website")),
                ("support_url", models.URLField(blank=True, verbose_name="support URL")),
                ("support_phone", models.CharField(blank=True, max_length=50, verbose_name="support phone")),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                ("is_active", models.BooleanField(default=True, verbose_name="active")),
            ],
            options={
                "verbose_name": "manufacturer",
                "verbose_name_plural": "manufacturers",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Supplier",
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
                ("name", models.CharField(max_length=150, unique=True, verbose_name="name")),
                (
                    "customer_number",
                    models.CharField(blank=True, max_length=50, verbose_name="customer number"),
                ),
                (
                    "contact_person",
                    models.CharField(blank=True, max_length=100, verbose_name="contact person"),
                ),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email")),
                ("phone", models.CharField(blank=True, max_length=50, verbose_name="phone")),
                ("website", models.URLField(blank=True, verbose_name="website")),
                ("address", models.TextField(blank=True, verbose_name="address")),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                ("is_active", models.BooleanField(default=True, verbose_name="active")),
            ],
            options={
                "verbose_name": "supplier",
                "verbose_name_plural": "suppliers",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Category",
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
                ("name", models.CharField(max_length=100, verbose_name="name")),
                (
                    "kind",
                    models.CharField(
                        choices=[("hardware", "Hardware"), ("software", "Software")],
                        default="hardware",
                        max_length=10,
                        verbose_name="type",
                    ),
                ),
                (
                    "item_name",
                    models.CharField(
                        blank=True,
                        help_text="Name of a single item, e.g. “Laptop”. Shown for “any model” requests.",
                        max_length=100,
                        verbose_name="singular name",
                    ),
                ),
                ("code", models.SlugField(blank=True, max_length=30, verbose_name="code")),
                ("description", models.TextField(blank=True, verbose_name="description")),
                (
                    "icon",
                    models.CharField(blank=True, help_text="Icon name", max_length=50, verbose_name="icon"),
                ),
                (
                    "is_requestable",
                    models.BooleanField(
                        default=True, help_text="Shown in the employee portal.", verbose_name="requestable"
                    ),
                ),
                (
                    "allow_any_model",
                    models.BooleanField(
                        default=True,
                        help_text="Employees may request “any device” of this group. Turn off where only a specific model makes sense, e.g. accessories or consumables.",
                        verbose_name="any model requestable",
                    ),
                ),
                (
                    "requires_approval",
                    models.BooleanField(
                        default=False,
                        help_text="Requests must first be approved by the employee's department. Applies to the subcategories as well.",
                        verbose_name="requires approval",
                    ),
                ),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="sort order")),
                (
                    "number_sequence",
                    models.ForeignKey(
                        blank=True,
                        help_text="Inventory numbers for new assets. Falls back to the parent category.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="categories",
                        to="core.numbersequence",
                        verbose_name="number sequence",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="children",
                        to="masterdata.category",
                        verbose_name="parent category",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        blank=True,
                        help_text="New requests and reports for this category go to this team. Falls back to the parent.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="categories",
                        to="accounts.team",
                        verbose_name="responsible team",
                    ),
                ),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="Location",
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
                ("name", models.CharField(max_length=100, verbose_name="name")),
                ("code", models.CharField(blank=True, max_length=30, verbose_name="code")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("site", "Site"),
                            ("building", "Building"),
                            ("room", "Room"),
                            ("storage", "Storage"),
                        ],
                        default="room",
                        max_length=10,
                        verbose_name="kind",
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="description")),
                (
                    "is_pickup_point",
                    models.BooleanField(
                        default=False,
                        help_text="Employees can collect devices here.",
                        verbose_name="pickup point",
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="children",
                        to="masterdata.location",
                        verbose_name="parent location",
                    ),
                ),
            ],
            options={
                "verbose_name": "location",
                "verbose_name_plural": "locations",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="AssetModel",
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
                ("name", models.CharField(max_length=150, verbose_name="name")),
                ("part_number", models.CharField(blank=True, max_length=100, verbose_name="part number")),
                (
                    "ean",
                    models.CharField(blank=True, db_index=True, max_length=14, verbose_name="EAN / GTIN"),
                ),
                (
                    "tracking",
                    models.CharField(
                        choices=[
                            ("serialized", "Individual devices"),
                            ("bulk", "Consumable (quantity)"),
                            ("license", "Software license"),
                        ],
                        default="serialized",
                        max_length=12,
                        verbose_name="tracking",
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="description")),
                ("specifications", models.TextField(blank=True, verbose_name="specifications")),
                (
                    "list_price",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="list price"
                    ),
                ),
                (
                    "warranty_months",
                    models.PositiveSmallIntegerField(default=24, verbose_name="warranty (months)"),
                ),
                ("is_requestable", models.BooleanField(default=True, verbose_name="requestable")),
                ("is_active", models.BooleanField(default=True, verbose_name="active")),
                (
                    "compatible_with",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Accessories, spare parts and consumables that fit this model.",
                        to="masterdata.assetmodel",
                        verbose_name="compatible with",
                    ),
                ),
                (
                    "team",
                    models.ForeignKey(
                        blank=True,
                        help_text="New requests and reports for this model go to this team. Empty: as the category.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="asset_models",
                        to="accounts.team",
                        verbose_name="responsible team",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="asset_models",
                        to="masterdata.category",
                        verbose_name="category",
                    ),
                ),
                (
                    "manufacturer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="asset_models",
                        to="masterdata.manufacturer",
                        verbose_name="manufacturer",
                    ),
                ),
                (
                    "default_supplier",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="asset_models",
                        to="masterdata.supplier",
                        verbose_name="default supplier",
                    ),
                ),
            ],
            options={
                "verbose_name": "model",
                "verbose_name_plural": "models",
                "ordering": ["manufacturer__name", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                condition=models.Q(("code", ""), _negated=True),
                fields=("code",),
                name="unique_category_code",
                violation_error_code="unique",
                violation_error_message="A category with this code already exists.",
            ),
        ),
        migrations.AddConstraint(
            model_name="assetmodel",
            constraint=models.UniqueConstraint(fields=("manufacturer", "name"), name="unique_model_name"),
        ),
    ]

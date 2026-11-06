import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0008_asset_model_predecessor"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="identifier_label",
            field=models.CharField(
                blank=True,
                help_text="What the identifier of devices is called in this category, e.g. “CN” or “MTM”. Not inherited by subcategories.",
                max_length=30,
                verbose_name="name of the identifier",
            ),
        ),
        migrations.CreateModel(
            name="ComponentType",
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
                ("name", models.CharField(max_length=100, unique=True, verbose_name="name")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="sort order")),
                (
                    "categories",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Devices of these categories and their subcategories have this part.",
                        related_name="component_types",
                        to="masterdata.category",
                        verbose_name="categories",
                    ),
                ),
            ],
            options={
                "verbose_name": "component type",
                "verbose_name_plural": "component types",
                "ordering": ["sort_order", "name"],
            },
        ),
    ]

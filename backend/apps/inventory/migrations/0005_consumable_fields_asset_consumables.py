import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_rename_stock_to_consumable"),
        ("masterdata", "0003_consumable_tracking_label"),
        ("procurement", "0002_stable_ordering"),
        ("reservations", "0004_rename_stock_item_to_consumable"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="consumable",
            options={
                "ordering": ["model__name"],
                "verbose_name": "consumable",
                "verbose_name_plural": "consumables",
            },
        ),
        migrations.AlterModelOptions(
            name="consumablemovement",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "consumable movement",
                "verbose_name_plural": "consumable movements",
            },
        ),
        migrations.AddField(
            model_name="asset",
            name="consumables",
            field=models.ManyToManyField(
                blank=True,
                help_text="Consumables for this device in addition to those compatible with its model.",
                limit_choices_to={"tracking": "bulk"},
                related_name="consuming_assets",
                to="masterdata.assetmodel",
                verbose_name="consumables",
            ),
        ),
        migrations.AlterField(
            model_name="consumable",
            name="location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="consumables",
                to="masterdata.location",
                verbose_name="location",
            ),
        ),
        migrations.AlterField(
            model_name="consumable",
            name="model",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="consumables",
                to="masterdata.assetmodel",
                verbose_name="model",
            ),
        ),
        migrations.AlterField(
            model_name="consumablemovement",
            name="consumable",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="movements",
                to="inventory.consumable",
                verbose_name="consumable",
            ),
        ),
        migrations.AlterField(
            model_name="consumablemovement",
            name="purchase_order_line",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="consumable_movements",
                to="procurement.purchaseorderline",
                verbose_name="purchase order line",
            ),
        ),
        migrations.AlterField(
            model_name="consumablemovement",
            name="recipient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="consumable_movements",
                to=settings.AUTH_USER_MODEL,
                verbose_name="recipient",
            ),
        ),
        migrations.AlterField(
            model_name="consumablemovement",
            name="reservation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="consumable_movements",
                to="reservations.reservation",
                verbose_name="reservation",
            ),
        ),
        migrations.AddConstraint(
            model_name="consumable",
            constraint=models.UniqueConstraint(
                fields=("model", "location"), name="unique_consumable_location"
            ),
        ),
    ]

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0005_consumable_fields_asset_consumables"),
        ("requests", "0004_rename_stock_item_to_consumable"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservationallocation",
            name="consumable",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reservation_allocations",
                to="inventory.consumable",
                verbose_name="consumable",
            ),
        ),
    ]

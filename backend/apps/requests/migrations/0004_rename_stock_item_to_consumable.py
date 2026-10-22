from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_rename_stock_to_consumable"),
        ("requests", "0003_stable_ordering"),
    ]

    operations = [
        migrations.RenameField(
            model_name="reservationallocation", old_name="stock_item", new_name="consumable"
        ),
    ]

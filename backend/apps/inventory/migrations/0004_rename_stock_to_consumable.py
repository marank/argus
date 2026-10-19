from django.db import migrations


class Migration(migrations.Migration):
    """Stock items become consumables; the data stays, only names change."""

    dependencies = [
        ("inventory", "0003_stable_ordering"),
        ("masterdata", "0002_category_allow_any_model"),
        ("procurement", "0002_stable_ordering"),
        ("reservations", "0003_stable_ordering"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="stockitem", name="unique_stock_location"),
        migrations.RenameModel(old_name="StockItem", new_name="Consumable"),
        migrations.RenameModel(old_name="StockMovement", new_name="ConsumableMovement"),
        migrations.RenameField(model_name="consumablemovement", old_name="stock_item", new_name="consumable"),
    ]

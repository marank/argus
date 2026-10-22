from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0002_item_description"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="reservationallocation",
            options={
                "ordering": ["allocated_at", "asset__inventory_number"],
                "verbose_name": "allocation",
                "verbose_name_plural": "allocations",
            },
        ),
        migrations.AlterModelOptions(
            name="reservationitem",
            options={
                "ordering": ["position"],
                "verbose_name": "reservation item",
                "verbose_name_plural": "reservation items",
            },
        ),
        migrations.AddField(
            model_name="reservationitem",
            name="position",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="position"),
        ),
    ]

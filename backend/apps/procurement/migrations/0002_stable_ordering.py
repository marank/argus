from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("procurement", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="purchaseorderline",
            options={
                "ordering": ["position"],
                "verbose_name": "order line",
                "verbose_name_plural": "order lines",
            },
        ),
        migrations.AddField(
            model_name="purchaseorderline",
            name="position",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="position"),
        ),
    ]

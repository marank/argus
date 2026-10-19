from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0002_category_allow_any_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assetmodel",
            name="tracking",
            field=models.CharField(
                choices=[("serialized", "Individual devices"), ("bulk", "Consumable (quantity)")],
                default="serialized",
                max_length=12,
                verbose_name="tracking",
            ),
        ),
    ]

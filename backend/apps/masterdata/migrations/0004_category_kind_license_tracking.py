from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0003_consumable_tracking_label"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="kind",
            field=models.CharField(
                choices=[("hardware", "Hardware"), ("software", "Software")],
                default="hardware",
                max_length=10,
                verbose_name="type",
            ),
        ),
        migrations.AlterField(
            model_name="assetmodel",
            name="tracking",
            field=models.CharField(
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
    ]

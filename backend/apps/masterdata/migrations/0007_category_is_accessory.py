from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0006_uuid7_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="is_accessory",
            field=models.BooleanField(
                default=False,
                help_text="Holds accessories, spare parts or consumables. In the employee portal its models appear with the devices they are compatible with. Applies to the subcategories as well.",
                verbose_name="accessories",
            ),
        ),
    ]

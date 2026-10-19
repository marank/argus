from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0004_category_kind_license_tracking"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="item_name",
            field=models.CharField(
                blank=True,
                help_text="Name of a single item, e.g. “Laptop”. Shown for “any model” requests.",
                max_length=100,
                verbose_name="singular name",
            ),
        ),
    ]

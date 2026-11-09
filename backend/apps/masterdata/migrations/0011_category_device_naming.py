import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_uuid7_ids"),
        ("masterdata", "0010_category_model_choice"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="device_naming",
            field=models.CharField(
                choices=[
                    ("none", "No name"),
                    ("sequence", "From a number sequence"),
                    ("inventory_number", "Same as the inventory number"),
                ],
                default="none",
                help_text="Name new devices get when none is entered, e.g. the hostname of PCs or the name of MDEs in the MDM. Not inherited by subcategories.",
                max_length=20,
                verbose_name="device names",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="name_sequence",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="core.numbersequence",
                verbose_name="number sequence for device names",
            ),
        ),
    ]

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        ("masterdata", "0004_category_sequence_not_inherited"),
    ]

    operations = [
        migrations.AddField(
            model_name="assetmodel",
            name="number_sequence",
            field=models.ForeignKey(
                blank=True,
                help_text="Inventory numbers for new devices of this model. Empty: the category's sequence, otherwise the general asset sequence.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_models",
                to="core.numbersequence",
                verbose_name="number sequence",
            ),
        ),
    ]

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
        ("masterdata", "0003_category_any_model_help"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="number_sequence",
            field=models.ForeignKey(
                blank=True,
                help_text="Inventory numbers for new assets. Not inherited by subcategories; without one, the general asset sequence applies.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="categories",
                to="core.numbersequence",
                verbose_name="number sequence",
            ),
        ),
    ]

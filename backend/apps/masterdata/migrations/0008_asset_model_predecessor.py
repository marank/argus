import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masterdata", "0007_category_is_accessory"),
    ]

    operations = [
        migrations.AddField(
            model_name="assetmodel",
            name="predecessor",
            field=models.ForeignKey(
                blank=True,
                help_text="The model this one replaces.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="successors",
                to="masterdata.assetmodel",
                verbose_name="successor of",
            ),
        ),
    ]

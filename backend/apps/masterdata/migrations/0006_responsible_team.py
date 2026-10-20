import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_team_is_default"),
        ("masterdata", "0005_category_item_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="assetmodel",
            name="team",
            field=models.ForeignKey(
                blank=True,
                help_text="New requests and reports for this model go to this team. Empty: as the category.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_models",
                to="accounts.team",
                verbose_name="responsible team",
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="team",
            field=models.ForeignKey(
                blank=True,
                help_text="New requests and reports for this category go to this team. Falls back to the parent.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="categories",
                to="accounts.team",
                verbose_name="responsible team",
            ),
        ),
    ]

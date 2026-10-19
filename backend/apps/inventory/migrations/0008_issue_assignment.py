import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_team"),
        ("inventory", "0007_asset_issues"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="assetissue",
            name="assigned_team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="issues",
                to="accounts.team",
                verbose_name="team",
            ),
        ),
        migrations.AddField(
            model_name="assetissue",
            name="assignee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_issues",
                to=settings.AUTH_USER_MODEL,
                verbose_name="assignee",
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_team_is_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="dashboard_settings",
            field=models.JSONField(blank=True, default=dict, verbose_name="dashboard layout"),
        ),
    ]

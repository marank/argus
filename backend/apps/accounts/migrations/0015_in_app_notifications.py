from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0014_sign_in_throttle"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="app_notification_settings",
            field=models.JSONField(blank=True, default=dict, verbose_name="in-app notifications"),
        ),
    ]

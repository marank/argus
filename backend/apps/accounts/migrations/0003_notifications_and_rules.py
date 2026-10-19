from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_ldap"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="notification_settings",
            field=models.JSONField(blank=True, default=dict, verbose_name="email notifications"),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_user_can_change_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="session_hours",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Empty: the duration from the site settings. E.g. longer for the pickup terminal.",
                null=True,
                verbose_name="session duration (hours)",
            ),
        ),
    ]

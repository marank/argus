from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_uuid7_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="session_hours",
            field=models.PositiveSmallIntegerField(
                default=12,
                help_text="How long a sign-in lasts; a user's own value overrides it.",
                verbose_name="session duration (hours)",
            ),
        ),
    ]

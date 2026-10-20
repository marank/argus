from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_team"),
    ]

    operations = [
        migrations.AddField(
            model_name="team",
            name="is_default",
            field=models.BooleanField(
                default=False,
                help_text="Gets new requests and reports that no category or model routes elsewhere.",
                verbose_name="default team",
            ),
        ),
    ]

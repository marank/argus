from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0002_uuid7_ids"),
    ]

    operations = [
        migrations.AddField(
            model_name="assetrequest",
            name="devices_unrecorded",
            field=models.BooleanField(
                default=False,
                help_text="Handed out without recording which devices; they can still be recorded.",
                verbose_name="devices not recorded",
            ),
        ),
    ]

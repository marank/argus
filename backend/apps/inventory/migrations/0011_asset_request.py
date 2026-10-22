import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0010_issue_conversation"),
        ("requests", "0019_asset_request"),
    ]

    operations = [
        migrations.RenameField("assetevent", "reservation", "asset_request"),
        migrations.RenameField("consumablemovement", "reservation", "asset_request"),
        migrations.AlterField(
            model_name="assetevent",
            name="asset_request",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_events",
                to="requests.assetrequest",
                verbose_name="request",
            ),
        ),
        migrations.AlterField(
            model_name="consumablemovement",
            name="asset_request",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="consumable_movements",
                to="requests.assetrequest",
                verbose_name="request",
            ),
        ),
    ]

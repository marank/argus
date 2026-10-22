import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("procurement", "0002_stable_ordering"),
        ("requests", "0019_asset_request"),
    ]

    operations = [
        migrations.RenameField("purchaseorderline", "reservation_item", "asset_request_item"),
        migrations.AlterField(
            model_name="purchaseorderline",
            name="asset_request_item",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order_lines",
                to="requests.assetrequestitem",
                verbose_name="for request line",
            ),
        ),
    ]

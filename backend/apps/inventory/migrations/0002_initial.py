import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("inventory", "0001_initial"),
        ("masterdata", "0001_initial"),
        ("procurement", "0001_initial"),
        ("requests", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="purchase_order_line",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assets",
                to="procurement.purchaseorderline",
                verbose_name="purchase order line",
            ),
        ),
        migrations.AddField(
            model_name="asset",
            name="supplier",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assets",
                to="masterdata.supplier",
                verbose_name="supplier",
            ),
        ),
        migrations.AddField(
            model_name="assetevent",
            name="asset",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to="inventory.asset",
                verbose_name="asset",
            ),
        ),
        migrations.AddField(
            model_name="assetevent",
            name="performed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="performed by",
            ),
        ),
        migrations.AddField(
            model_name="assetevent",
            name="related_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_events",
                to=settings.AUTH_USER_MODEL,
                verbose_name="employee",
            ),
        ),
        migrations.AddField(
            model_name="assetevent",
            name="reservation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_events",
                to="requests.reservation",
                verbose_name="reservation",
            ),
        ),
        migrations.AddField(
            model_name="stockitem",
            name="location",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="stock_items",
                to="masterdata.location",
                verbose_name="location",
            ),
        ),
        migrations.AddField(
            model_name="stockitem",
            name="model",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="stock_items",
                to="masterdata.assetmodel",
                verbose_name="model",
            ),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="performed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="performed by",
            ),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="purchase_order_line",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stock_movements",
                to="procurement.purchaseorderline",
                verbose_name="purchase order line",
            ),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="recipient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stock_movements",
                to=settings.AUTH_USER_MODEL,
                verbose_name="recipient",
            ),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="reservation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stock_movements",
                to="requests.reservation",
                verbose_name="reservation",
            ),
        ),
        migrations.AddField(
            model_name="stockmovement",
            name="stock_item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="movements",
                to="inventory.stockitem",
                verbose_name="stock item",
            ),
        ),
        migrations.AddConstraint(
            model_name="asset",
            constraint=models.UniqueConstraint(
                condition=models.Q(("serial_number", ""), _negated=True),
                fields=("model", "serial_number"),
                name="unique_serial_per_model",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockitem",
            constraint=models.UniqueConstraint(fields=("model", "location"), name="unique_stock_location"),
        ),
    ]

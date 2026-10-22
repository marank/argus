import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_in_app_notifications"),
        ("inventory", "0010_issue_conversation"),
        ("requests", "0018_quick_assignment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel("Reservation", "AssetRequest"),
        migrations.RenameModel("ReservationItem", "AssetRequestItem"),
        migrations.RenameModel("ReservationAllocation", "AssetRequestAllocation"),
        migrations.RenameModel("ReservationEvent", "AssetRequestEvent"),
        migrations.RenameField("assetrequestitem", "reservation", "asset_request"),
        migrations.RenameField("assetrequestevent", "reservation", "asset_request"),
        migrations.RenameField("handover", "reservation", "asset_request"),
        migrations.RenameField("devicereturn", "reservation", "asset_request"),
        migrations.AlterModelOptions(
            name="assetrequest",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "request",
                "verbose_name_plural": "requests",
            },
        ),
        migrations.AlterModelOptions(
            name="assetrequestitem",
            options={
                "ordering": ["position"],
                "verbose_name": "request line",
                "verbose_name_plural": "request lines",
            },
        ),
        migrations.AlterField(
            model_name="assetrequest",
            name="assigned_team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_requests",
                to="accounts.team",
                verbose_name="team",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequest",
            name="assignee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_asset_requests",
                to=settings.AUTH_USER_MODEL,
                verbose_name="assignee",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequest",
            name="handled_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="handled_asset_requests",
                to=settings.AUTH_USER_MODEL,
                verbose_name="handled by",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequest",
            name="requester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="asset_requests",
                to=settings.AUTH_USER_MODEL,
                verbose_name="requester",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestallocation",
            name="asset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="asset_request_allocations",
                to="inventory.asset",
                verbose_name="asset",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestallocation",
            name="consumable",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="asset_request_allocations",
                to="inventory.consumable",
                verbose_name="consumable",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestallocation",
            name="item",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="allocations",
                to="requests.assetrequestitem",
                verbose_name="request line",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestallocation",
            name="license",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="asset_request_allocations",
                to="inventory.license",
                verbose_name="license",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestallocation",
            name="license_assignment",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="asset_request_allocation",
                to="inventory.licenseassignment",
                verbose_name="license assignment",
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestitem",
            name="asset_request",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="requests.assetrequest",
                verbose_name="request",
            ),
        ),
        migrations.AlterField(
            model_name="devicereturn",
            name="asset_request",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="returns",
                to="requests.assetrequest",
                verbose_name="request",
            ),
        ),
        migrations.AlterField(
            model_name="handover",
            name="asset_request",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="handover",
                to="requests.assetrequest",
                verbose_name="request",
            ),
        ),
    ]

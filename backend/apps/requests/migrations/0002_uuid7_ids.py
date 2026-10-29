import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assetrequest",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestallocation",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestevent",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="assetrequestitem",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="devicereturn",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="handover",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]

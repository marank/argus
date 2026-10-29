import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mailsettings",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="notificationlog",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="numbersequence",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="sitesettings",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]

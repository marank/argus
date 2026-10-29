import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="asset",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="assetevent",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="assetissue",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="assetissueentry",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="consumable",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="consumablemovement",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="license",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="licenseassignment",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]

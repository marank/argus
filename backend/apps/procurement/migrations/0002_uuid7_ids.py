import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("procurement", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchaseorder",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="purchaseorderline",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid7, editable=False, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]

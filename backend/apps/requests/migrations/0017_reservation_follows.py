import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0016_backfill_reservation_events"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="follows",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="requests.reservation",
                verbose_name="follows",
            ),
        ),
    ]

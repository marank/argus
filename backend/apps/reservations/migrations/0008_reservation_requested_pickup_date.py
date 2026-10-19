from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0007_handover_mode_collect"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="requested_pickup_date",
            field=models.DateField(blank=True, null=True, verbose_name="preferred pickup day"),
        ),
    ]

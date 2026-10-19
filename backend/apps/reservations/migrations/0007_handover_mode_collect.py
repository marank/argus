from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0006_reservation_skip_device_check"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservation",
            name="handover_mode",
            field=models.CharField(
                choices=[
                    ("pickup", "Pickup with signature"),
                    ("collect", "Simple pickup"),
                    ("delivery", "Delivered by IT"),
                ],
                default="pickup",
                help_text="Pickup requests appear on the pickup terminal once they are ready.",
                max_length=10,
                verbose_name="handover",
            ),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0005_allocation_consumable_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="skip_device_check",
            field=models.BooleanField(
                default=False,
                help_text="The pickup terminal starts with who collects, without checking the devices.",
                verbose_name="skip device check",
            ),
        ),
    ]

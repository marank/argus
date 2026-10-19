from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservationitem",
            name="description",
            field=models.CharField(
                blank=True,
                help_text="Free text for something that is not in the catalog.",
                max_length=255,
                verbose_name="description",
            ),
        ),
    ]

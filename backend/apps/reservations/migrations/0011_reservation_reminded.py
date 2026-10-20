import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0010_reservation_assignment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="reminded_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When IT last reminded the employee to return the devices.",
                null=True,
                verbose_name="reminded at",
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="reminded_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="reminded by",
            ),
        ),
    ]

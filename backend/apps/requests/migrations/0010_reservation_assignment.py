import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_team"),
        ("requests", "0009_licenses_returns_prepared_by"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="assigned_team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reservations",
                to="accounts.team",
                verbose_name="team",
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="assignee",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_reservations",
                to=settings.AUTH_USER_MODEL,
                verbose_name="assignee",
            ),
        ),
    ]

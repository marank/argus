"""IT *confirms* a request; "approval" is reserved for the department's approver."""

from django.db import migrations, models


def rename_status(apps, old, new):
    Reservation = apps.get_model("reservations", "Reservation")
    Reservation.objects.filter(status=old).update(status=new)


def forwards(apps, schema_editor):
    rename_status(apps, "approved", "confirmed")


def backwards(apps, schema_editor):
    rename_status(apps, "confirmed", "approved")


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0011_reservation_reminded"),
    ]

    operations = [
        migrations.RenameField(model_name="reservation", old_name="approved_at", new_name="confirmed_at"),
        migrations.AlterField(
            model_name="reservation",
            name="confirmed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="confirmed at"),
        ),
        migrations.RenameField(
            model_name="reservationitem", old_name="quantity_approved", new_name="quantity_confirmed"
        ),
        migrations.AlterField(
            model_name="reservationitem",
            name="quantity_confirmed",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="confirmed quantity"),
        ),
        migrations.AlterField(
            model_name="reservation",
            name="status",
            field=models.CharField(
                choices=[
                    ("submitted", "Submitted"),
                    ("confirmed", "Confirmed"),
                    ("ready", "Ready for pickup"),
                    ("handed_out", "Handed out"),
                    ("completed", "Completed"),
                    ("rejected", "Rejected"),
                    ("cancelled", "Cancelled"),
                ],
                db_index=True,
                default="submitted",
                max_length=12,
                verbose_name="status",
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]

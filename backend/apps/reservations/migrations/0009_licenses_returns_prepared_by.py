import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def fill_handover_people(apps, schema_editor):
    """Terminal hand-outs named the terminal account; credit the IT member who prepared them."""
    Handover = apps.get_model("reservations", "Handover")
    Reservation = apps.get_model("reservations", "Reservation")
    for reservation in Reservation.objects.filter(status__in=["ready", "handed_out", "completed"]):
        if reservation.handled_by_id:
            reservation.prepared_by_id = reservation.handled_by_id
            reservation.save(update_fields=["prepared_by"])
    for handover in Handover.objects.select_related("reservation"):
        handover.recorded_by_id = handover.handed_out_by_id
        if handover.method == "signature":
            handover.handed_out_by_id = handover.reservation.handled_by_id
        handover.save(update_fields=["recorded_by", "handed_out_by"])


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0007_asset_issues"),
        ("reservations", "0008_reservation_requested_pickup_date"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="handover",
            name="recorded_by",
            field=models.ForeignKey(
                blank=True,
                help_text="The account the hand-out was recorded with, e.g. the pickup terminal.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="recorded by",
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="prepared_by",
            field=models.ForeignKey(
                blank=True,
                help_text="Who marked the request ready; shown as handing out at the pickup terminal.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="prepared by",
            ),
        ),
        migrations.AddField(
            model_name="reservationallocation",
            name="license",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reservation_allocations",
                to="inventory.license",
                verbose_name="license",
            ),
        ),
        migrations.AddField(
            model_name="reservationallocation",
            name="license_assignment",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reservation_allocation",
                to="inventory.licenseassignment",
                verbose_name="license assignment",
            ),
        ),
        migrations.AddField(
            model_name="reservationallocation",
            name="return_note",
            field=models.CharField(
                blank=True,
                help_text="E.g. the condition when it came back.",
                max_length=255,
                verbose_name="return note",
            ),
        ),
        migrations.CreateModel(
            name="DeviceReturn",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                ("returned_at", models.DateTimeField(auto_now_add=True, verbose_name="returned at")),
                (
                    "reservation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="returns",
                        to="reservations.reservation",
                        verbose_name="reservation",
                    ),
                ),
                (
                    "returned_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="taken back by",
                    ),
                ),
            ],
            options={
                "verbose_name": "return",
                "verbose_name_plural": "returns",
                "ordering": ["returned_at"],
            },
        ),
        migrations.AddField(
            model_name="reservationallocation",
            name="device_return",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="allocations",
                to="reservations.devicereturn",
                verbose_name="return",
            ),
        ),
        migrations.AddField(
            model_name="reservationallocation",
            name="returned_damaged",
            field=models.BooleanField(default=False, verbose_name="returned damaged"),
        ),
        migrations.RunPython(fill_handover_people, migrations.RunPython.noop),
    ]

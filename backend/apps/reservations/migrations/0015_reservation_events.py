import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0014_direct_hand_out"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ReservationEvent",
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
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("created", "Requested"),
                            ("direct", "Direct hand-out recorded"),
                            ("approved", "Approved"),
                            ("declined", "Not approved"),
                            ("confirmed", "Confirmed"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                            ("assigned", "Assignment changed"),
                            ("allocated", "Allocated"),
                            ("released", "Allocation removed"),
                            ("ready", "Ready for pickup"),
                            ("reopened", "Back in preparation"),
                            ("rescheduled", "Handover changed"),
                            ("handed_out", "Handed out"),
                            ("returned", "Taken back"),
                            ("extended", "Loan extended"),
                            ("reminded", "Reminded to return"),
                            ("completed", "Completed"),
                        ],
                        max_length=20,
                        verbose_name="kind",
                    ),
                ),
                (
                    "at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="at"),
                ),
                ("data", models.JSONField(blank=True, default=dict, verbose_name="details")),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="by",
                    ),
                ),
                (
                    "reservation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="reservations.reservation",
                        verbose_name="request",
                    ),
                ),
            ],
            options={
                "verbose_name": "request event",
                "verbose_name_plural": "request events",
                "ordering": ["at"],
            },
        ),
    ]

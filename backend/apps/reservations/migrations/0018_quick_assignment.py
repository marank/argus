from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0017_reservation_follows"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reservation",
            name="origin",
            field=models.CharField(
                choices=[
                    ("request", "Request"),
                    ("direct", "Direct hand-out"),
                    ("quick", "Quick assignment"),
                ],
                default="request",
                max_length=10,
                verbose_name="origin",
            ),
        ),
        migrations.AlterField(
            model_name="reservationevent",
            name="kind",
            field=models.CharField(
                choices=[
                    ("created", "Requested"),
                    ("direct", "Direct hand-out recorded"),
                    ("quick", "Quick assignment recorded"),
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
    ]

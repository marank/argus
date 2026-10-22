import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("requests", "0012_confirm_instead_of_approve"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="approval",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Not required"),
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="",
                max_length=10,
                verbose_name="approval",
            ),
        ),
        migrations.AddField(
            model_name="reservation",
            name="approval_comment",
            field=models.TextField(blank=True, verbose_name="approval comment"),
        ),
        migrations.AddField(
            model_name="reservation",
            name="approval_decided_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="approval decided at"),
        ),
        migrations.AddField(
            model_name="reservation",
            name="approver",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="approver",
            ),
        ),
        migrations.AlterField(
            model_name="reservation",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending_approval", "Awaiting approval"),
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
                max_length=20,
                verbose_name="status",
            ),
        ),
    ]

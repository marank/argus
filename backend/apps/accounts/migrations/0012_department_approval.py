from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_confirm_instead_of_approve"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="approvers",
            field=models.ManyToManyField(
                blank=True,
                help_text="Approve requests of the department's members for categories that need approval. Without approvers such requests go straight to IT.",
                related_name="approving_departments",
                to=settings.AUTH_USER_MODEL,
                verbose_name="approvers",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="approval_exempt",
            field=models.BooleanField(
                default=False,
                help_text="Requests go straight to IT, even for categories that need approval.",
                verbose_name="exempt from approval",
            ),
        ),
    ]

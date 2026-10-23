import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="department",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="children",
                to="accounts.department",
                verbose_name="parent department",
            ),
        ),
        migrations.AlterField(
            model_name="department",
            name="approvers",
            field=models.ManyToManyField(
                blank=True,
                help_text="Approve requests of the department's members for categories that need approval. Without approvers those of the parent department apply; without any, such requests go straight to IT.",
                related_name="approving_departments",
                to=settings.AUTH_USER_MODEL,
                verbose_name="approvers",
            ),
        ),
    ]

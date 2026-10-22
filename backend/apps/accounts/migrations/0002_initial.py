import django.db.models.deletion
import django.db.models.functions.text
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("masterdata", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="terminal_location",
            field=models.ForeignKey(
                blank=True,
                help_text="Pickup terminal only: lists pickups at this location and below; empty lists all.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="masterdata.location",
                verbose_name="terminal site",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="user_permissions",
            field=models.ManyToManyField(
                blank=True,
                help_text="Specific permissions for this user.",
                related_name="user_set",
                related_query_name="user",
                to="auth.permission",
                verbose_name="user permissions",
            ),
        ),
        migrations.AddField(
            model_name="backupcode",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="backup_codes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
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
            name="department",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="members",
                to="accounts.department",
                verbose_name="department",
            ),
        ),
        migrations.AddField(
            model_name="role",
            name="members",
            field=models.ManyToManyField(
                blank=True, related_name="roles", to=settings.AUTH_USER_MODEL, verbose_name="members"
            ),
        ),
        migrations.AddField(
            model_name="team",
            name="members",
            field=models.ManyToManyField(
                blank=True, related_name="teams", to=settings.AUTH_USER_MODEL, verbose_name="members"
            ),
        ),
        migrations.AddField(
            model_name="twofactor",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="two_factor",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("username"),
                name="unique_username_ignoring_case",
                violation_error_message="A user with this username already exists.",
            ),
        ),
    ]

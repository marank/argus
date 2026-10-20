import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0009_user_dashboard_settings"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupCode",
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
                ("salt", models.CharField(editable=False, max_length=32)),
                ("code_hash", models.CharField(editable=False, max_length=64)),
                (
                    "used_at",
                    models.DateTimeField(blank=True, editable=False, null=True, verbose_name="used at"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="backup_codes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "backup code",
                "verbose_name_plural": "backup codes",
            },
        ),
        migrations.CreateModel(
            name="TwoFactor",
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
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                (
                    "method",
                    models.CharField(
                        choices=[("email", "Code by email"), ("totp", "Authenticator app")],
                        max_length=10,
                        verbose_name="method",
                    ),
                ),
                (
                    "totp_secret",
                    models.CharField(blank=True, editable=False, max_length=64, verbose_name="app secret"),
                ),
                ("totp_last_step", models.BigIntegerField(default=0, editable=False)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="two_factor",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "two-factor sign-in",
                "verbose_name_plural": "two-factor sign-ins",
            },
        ),
    ]

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_site_settings"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MailSettings",
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
                ("enabled", models.BooleanField(default=False, verbose_name="send emails")),
                ("host", models.CharField(blank=True, max_length=255, verbose_name="SMTP server")),
                ("port", models.PositiveIntegerField(default=587, verbose_name="port")),
                (
                    "security",
                    models.CharField(
                        choices=[("starttls", "STARTTLS"), ("ssl", "SSL/TLS"), ("none", "None")],
                        default="starttls",
                        max_length=10,
                        verbose_name="encryption",
                    ),
                ),
                ("username", models.CharField(blank=True, max_length=255, verbose_name="user name")),
                ("password", models.CharField(blank=True, max_length=255, verbose_name="password")),
                ("from_email", models.EmailField(blank=True, max_length=254, verbose_name="sender address")),
                ("from_name", models.CharField(default="Argus", max_length=100, verbose_name="sender name")),
                (
                    "app_url",
                    models.URLField(
                        blank=True,
                        help_text="Address of Argus for links in emails, e.g. https://argus.example.com",
                        verbose_name="app address",
                    ),
                ),
                ("events", models.JSONField(blank=True, default=dict, verbose_name="notifications")),
            ],
            options={
                "verbose_name": "mail settings",
                "verbose_name_plural": "mail settings",
            },
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="default_loan_days",
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text="Suggested length of a temporary request.",
                verbose_name="default loan period (days)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="license_warning_days",
            field=models.PositiveSmallIntegerField(
                default=60,
                help_text="Licenses ending within this many days count as ending soon.",
                verbose_name="license warning (days)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="max_loan_days",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Longest allowed temporary request; 0 = no limit.",
                verbose_name="maximum loan period (days)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="return_reminder_days",
            field=models.PositiveSmallIntegerField(
                default=2,
                help_text="Employees are reminded this many days before a return is due.",
                verbose_name="return reminder (days before)",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="warranty_warning_days",
            field=models.PositiveSmallIntegerField(
                default=60,
                help_text="Warranties ending within this many days count as ending soon.",
                verbose_name="warranty warning (days)",
            ),
        ),
        migrations.CreateModel(
            name="NotificationLog",
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
                ("event", models.CharField(max_length=40, verbose_name="notification")),
                ("key", models.CharField(max_length=200, verbose_name="key")),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="recipient",
                    ),
                ),
            ],
            options={
                "verbose_name": "sent notification",
                "verbose_name_plural": "sent notifications",
                "ordering": ["-created_at"],
                "constraints": [
                    models.UniqueConstraint(fields=("event", "key", "recipient"), name="unique_notification")
                ],
            },
        ),
    ]

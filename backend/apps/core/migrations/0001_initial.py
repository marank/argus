import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# The sequences Argus draws from by code (see apps.core.services.numbering).
SYSTEM_SEQUENCES = {
    "asset": {"name": "Assets", "prefix": "INV", "pattern": "{prefix}-{seq}", "padding": 6},
    "request": {
        "name": "Requests",
        "prefix": "RES",
        "pattern": "{prefix}-{year}-{seq}",
        "padding": 5,
        "reset_period": "yearly",
    },
    "purchase-order": {
        "name": "Purchase orders",
        "prefix": "PO",
        "pattern": "{prefix}-{year}-{seq}",
        "padding": 4,
        "reset_period": "yearly",
    },
}


def create_system_sequences(apps, schema_editor):
    """Creates the system sequences up front, so they can be set up before the first number."""
    NumberSequence = apps.get_model("core", "NumberSequence")
    for code, defaults in SYSTEM_SEQUENCES.items():
        NumberSequence.objects.get_or_create(code=code, defaults={**defaults, "is_system": True})


class Migration(migrations.Migration):
    initial = True

    dependencies = [
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
                ("events", models.JSONField(blank=True, default=dict, verbose_name="email notifications")),
                (
                    "app_events",
                    models.JSONField(blank=True, default=dict, verbose_name="in-app notifications"),
                ),
            ],
            options={
                "verbose_name": "mail settings",
                "verbose_name_plural": "mail settings",
            },
        ),
        migrations.CreateModel(
            name="SiteSettings",
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
                ("flags", models.JSONField(blank=True, default=dict, verbose_name="modules and features")),
                (
                    "warranty_warning_days",
                    models.PositiveSmallIntegerField(
                        default=60,
                        help_text="Warranties ending within this many days count as ending soon.",
                        verbose_name="warranty warning (days)",
                    ),
                ),
                (
                    "license_warning_days",
                    models.PositiveSmallIntegerField(
                        default=60,
                        help_text="Licenses ending within this many days count as ending soon.",
                        verbose_name="license warning (days)",
                    ),
                ),
                (
                    "default_loan_days",
                    models.PositiveSmallIntegerField(
                        default=5,
                        help_text="Suggested length of a temporary request.",
                        verbose_name="default loan period (days)",
                    ),
                ),
                (
                    "max_loan_days",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Longest allowed temporary request; 0 = no limit.",
                        verbose_name="maximum loan period (days)",
                    ),
                ),
                (
                    "return_reminder_days",
                    models.PositiveSmallIntegerField(
                        default=2,
                        help_text="Employees are reminded this many days before a return is due.",
                        verbose_name="return reminder (days before)",
                    ),
                ),
            ],
            options={
                "verbose_name": "site settings",
                "verbose_name_plural": "site settings",
            },
        ),
        migrations.CreateModel(
            name="NumberSequence",
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
                ("code", models.SlugField(blank=True, verbose_name="code")),
                ("name", models.CharField(max_length=100, verbose_name="name")),
                ("prefix", models.CharField(blank=True, max_length=20, verbose_name="prefix")),
                (
                    "pattern",
                    models.CharField(default="{prefix}{seq}", max_length=100, verbose_name="pattern"),
                ),
                ("padding", models.PositiveSmallIntegerField(default=5, verbose_name="padding")),
                ("next_value", models.PositiveIntegerField(default=1, verbose_name="next value")),
                (
                    "reset_period",
                    models.CharField(
                        choices=[("never", "Never"), ("yearly", "Yearly"), ("monthly", "Monthly")],
                        default="never",
                        max_length=10,
                        verbose_name="reset period",
                    ),
                ),
                (
                    "period_key",
                    models.CharField(
                        blank=True, editable=False, max_length=10, verbose_name="current period"
                    ),
                ),
                (
                    "is_system",
                    models.BooleanField(default=False, editable=False, verbose_name="system sequence"),
                ),
            ],
            options={
                "verbose_name": "number sequence",
                "verbose_name_plural": "number sequences",
                "ordering": ["name"],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("code", ""), _negated=True),
                        fields=("code",),
                        name="unique_number_sequence_code",
                        violation_error_code="unique",
                        violation_error_message="A number sequence with this code already exists.",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Notification",
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
                ("key", models.CharField(blank=True, max_length=200, verbose_name="key")),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                ("text", models.TextField(blank=True, verbose_name="text")),
                ("path", models.CharField(blank=True, max_length=300, verbose_name="link")),
                ("read_at", models.DateTimeField(blank=True, null=True, verbose_name="read at")),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="recipient",
                    ),
                ),
            ],
            options={
                "verbose_name": "in-app notification",
                "verbose_name_plural": "in-app notifications",
                "ordering": ["-created_at"],
                "indexes": [models.Index(fields=["recipient", "read_at"], name="notification_unread")],
            },
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
        migrations.RunPython(create_system_sequences, migrations.RunPython.noop),
    ]

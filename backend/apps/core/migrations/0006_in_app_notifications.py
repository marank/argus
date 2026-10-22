import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_request_sequence_hyphen_in_pattern"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="mailsettings",
            name="app_events",
            field=models.JSONField(blank=True, default=dict, verbose_name="in-app notifications"),
        ),
        migrations.AlterField(
            model_name="mailsettings",
            name="events",
            field=models.JSONField(blank=True, default=dict, verbose_name="email notifications"),
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
    ]

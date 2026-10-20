import uuid
from datetime import timedelta

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def fill_entries(apps, schema_editor):
    """Turn what reports recorded so far into entries: IT's current status and its answer."""
    AssetIssue = apps.get_model("inventory", "AssetIssue")
    Entry = apps.get_model("inventory", "AssetIssueEntry")
    for issue in AssetIssue.objects.exclude(status="open"):
        at = issue.resolved_at or issue.updated_at
        entries = []
        if issue.resolution:
            entries.append(
                Entry(issue=issue, kind="message", author_id=issue.handled_by_id, text=issue.resolution)
            )
        entries.append(Entry(issue=issue, kind="status", author_id=issue.handled_by_id, status=issue.status))
        # The answer just before the status; auto_now_add would stamp both with today.
        for offset, entry in enumerate(reversed(entries)):
            entry.save()
            stamp = at - timedelta(seconds=offset)
            Entry.objects.filter(pk=entry.pk).update(created_at=stamp, updated_at=stamp)


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0009_issue_unseen_update"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetIssueEntry",
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
                    "kind",
                    models.CharField(
                        choices=[("message", "Message"), ("status", "Change of status")],
                        max_length=10,
                        verbose_name="kind",
                    ),
                ),
                ("text", models.TextField(blank=True, verbose_name="text")),
                (
                    "status",
                    models.CharField(
                        blank=True,
                        choices=[("open", "Open"), ("in_progress", "In progress"), ("resolved", "Resolved")],
                        max_length=12,
                        verbose_name="status",
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="author",
                    ),
                ),
                (
                    "issue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="entries",
                        to="inventory.assetissue",
                        verbose_name="problem report",
                    ),
                ),
            ],
            options={
                "verbose_name": "problem report entry",
                "verbose_name_plural": "problem report entries",
                "ordering": ["created_at"],
            },
        ),
        migrations.RunPython(fill_entries, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="assetissue",
            name="resolution",
        ),
    ]

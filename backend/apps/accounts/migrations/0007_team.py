import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_user_terminal_location"),
    ]

    operations = [
        migrations.CreateModel(
            name="Team",
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
                ("name", models.CharField(max_length=100, unique=True, verbose_name="name")),
                ("code", models.CharField(blank=True, max_length=20, verbose_name="code")),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Lower numbers come first; equal numbers by name.",
                        verbose_name="sort order",
                    ),
                ),
                (
                    "ldap_group_dn",
                    models.CharField(
                        blank=True,
                        help_text="DN of a directory group; its members join the team when they sign in.",
                        max_length=500,
                        verbose_name="LDAP group",
                    ),
                ),
                (
                    "members",
                    models.ManyToManyField(
                        blank=True, related_name="teams", to=settings.AUTH_USER_MODEL, verbose_name="members"
                    ),
                ),
            ],
            options={
                "verbose_name": "team",
                "verbose_name_plural": "teams",
                "ordering": ["sort_order", "name"],
            },
        ),
    ]

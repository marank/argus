import uuid

from django.conf import settings
from django.db import migrations, models

# The areas as of this migration; IT staff keep everything they could do before.
FULL_ACCESS = {
    key: "write"
    for key in (
        "models",
        "categories",
        "manufacturers",
        "suppliers",
        "locations",
        "departments",
        "teams",
        "users",
        "number_sequences",
        "reservations",
        "assets",
        "consumables",
        "licenses",
        "issues",
        "procurement",
    )
}


def grant_full_access(apps, schema_editor):
    """Existing IT staff get a role with full access, so introducing roles takes nothing away."""
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")
    staff = User.objects.filter(is_staff=True, is_superuser=False, is_terminal=False)
    if not staff.exists():
        return
    role = Role.objects.create(
        name="Vollzugriff",
        description="Alles lesen und bearbeiten (bei der Einführung der Rollen angelegt).",
        permissions=FULL_ACCESS,
    )
    role.members.set(staff)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_department_approval"),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
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
                ("description", models.TextField(blank=True, verbose_name="description")),
                ("permissions", models.JSONField(blank=True, default=dict, verbose_name="permissions")),
                (
                    "members",
                    models.ManyToManyField(
                        blank=True, related_name="roles", to=settings.AUTH_USER_MODEL, verbose_name="members"
                    ),
                ),
            ],
            options={
                "verbose_name": "role",
                "verbose_name_plural": "roles",
                "ordering": ["name"],
            },
        ),
        migrations.RunPython(grant_full_access, migrations.RunPython.noop),
    ]

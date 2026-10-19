import django.db.models.functions.text
from django.db import migrations, models
from django.db.models import Count
from django.db.models.functions import Lower

import apps.accounts.models.user


def refuse_case_duplicates(apps, schema_editor):
    """Stop with a readable message if usernames differ only in case (e.g. Anna / anna)."""
    User = apps.get_model("accounts", "User")
    clashes = (
        User.objects.annotate(name=Lower("username"))
        .values("name")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    if clashes:
        names = sorted(
            User.objects.annotate(name=Lower("username"))
            .filter(name__in=[c["name"] for c in clashes])
            .values_list("username", flat=True)
        )
        raise RuntimeError(
            "These usernames differ only in upper/lower case: "
            + ", ".join(names)
            + ". Merge or rename them (e.g. in the Django admin) and run the migration again."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_notifications_and_rules"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(refuse_case_duplicates, migrations.RunPython.noop),
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", apps.accounts.models.user.CaseInsensitiveUserManager()),
            ],
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

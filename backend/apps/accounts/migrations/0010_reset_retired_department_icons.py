from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

RETIRED_ICONS = ["shirt", "footprints", "gem", "baby", "scissors"]


def reset_icons(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Departments with an icon that is no longer offered get the building."""
    department = apps.get_model("accounts", "Department")
    department.objects.filter(icon__in=RETIRED_ICONS).update(icon="building")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0009_approval_delegation")]

    operations = [migrations.RunPython(reset_icons, migrations.RunPython.noop)]

from django.db import migrations


def _rename_area(apps, old: str, new: str) -> None:
    Role = apps.get_model("accounts", "Role")
    for role in Role.objects.all():
        if old in role.permissions:
            role.permissions[new] = role.permissions.pop(old)
            role.save(update_fields=["permissions"])


def forward(apps, schema_editor):
    _rename_area(apps, "reservations", "requests")


def backward(apps, schema_editor):
    _rename_area(apps, "requests", "reservations")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0015_in_app_notifications"),
    ]

    operations = [migrations.RunPython(forward, backward)]

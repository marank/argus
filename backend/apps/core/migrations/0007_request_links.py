from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Concat, Substr


def _move_links(apps, old: str, new: str) -> None:
    # Notifications link to the request's page, which moved from /reservations/ to /requests/.
    Notification = apps.get_model("core", "Notification")
    Notification.objects.filter(path__startswith=old).update(
        path=Concat(Value(new), Substr("path", len(old) + 1))
    )


def forward(apps, schema_editor):
    _move_links(apps, "/reservations/", "/requests/")


def backward(apps, schema_editor):
    _move_links(apps, "/requests/", "/reservations/")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_in_app_notifications"),
    ]

    operations = [migrations.RunPython(forward, backward)]

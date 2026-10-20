"""Stored keys follow the rename of IT's "approve" step to "confirm"."""

import json

from django.db import migrations

RENAMES = {"request_approved": "request_confirmed", "to_approve": "to_confirm"}


def _rename(keys, renames):
    return [renames.get(key, key) for key in keys] if isinstance(keys, list) else keys


def migrate(apps, renames):
    User = apps.get_model("accounts", "User")
    for user in User.objects.all().only("id", "notification_settings", "dashboard_settings"):
        before = (json.dumps(user.notification_settings), json.dumps(user.dashboard_settings))
        user.notification_settings = {
            renames.get(k, k): v for k, v in (user.notification_settings or {}).items()
        }
        for widget in (user.dashboard_settings or {}).get("widgets") or []:
            if isinstance(widget, dict):
                for field in ("hidden_cards", "card_order"):
                    if field in widget:
                        widget[field] = _rename(widget[field], renames)
        if before != (json.dumps(user.notification_settings), json.dumps(user.dashboard_settings)):
            user.save(update_fields=["notification_settings", "dashboard_settings"])


def forwards(apps, schema_editor):
    migrate(apps, RENAMES)


def backwards(apps, schema_editor):
    migrate(apps, {new: old for old, new in RENAMES.items()})


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_two_factor"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]

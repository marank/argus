"""Battery replacements become replacements of the tracked part "Battery".

The separate event kind is gone: any tracked part (see masterdata.ComponentType) is replaced
with "component replaced". Existing battery events keep their text and are linked to a
component type "Battery", created when there are any (rename it as you like).
"""

from django.db import migrations


def forwards(apps, schema_editor):
    AssetEvent = apps.get_model("inventory", "AssetEvent")
    ComponentType = apps.get_model("masterdata", "ComponentType")
    events = AssetEvent.objects.filter(kind="battery_replaced")
    if not events.exists():
        return
    battery, _ = ComponentType.objects.get_or_create(name="Battery")
    events.update(kind="component_replaced", component_type=battery)


def backwards(apps, schema_editor):
    AssetEvent = apps.get_model("inventory", "AssetEvent")
    AssetEvent.objects.filter(kind="component_replaced", component_type__name="Battery").update(
        kind="battery_replaced"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_asset_identifier_assetevent_component_type_and_more"),
        ("masterdata", "0009_category_identifier_label_componenttype"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]

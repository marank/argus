"""MAC addresses are stored as AA:BB:CC:DD:EE:FF.

Existing addresses written another way ("aa-bb-cc-dd-ee-ff", "AABBCCDDEEFF") are brought into
that form; ones that are not twelve hex digits stay as they are until the device is edited.
"""

import django.core.validators
from django.db import migrations, models

from apps.inventory.services.mac_address import normalize_mac_address


def forwards(apps, schema_editor):
    Asset = apps.get_model("inventory", "Asset")
    for asset in Asset.objects.exclude(mac_address="").only("pk", "mac_address"):
        normalized = normalize_mac_address(asset.mac_address)
        if normalized != asset.mac_address:
            Asset.objects.filter(pk=asset.pk).update(mac_address=normalized)


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0005_battery_events_to_components"),
    ]

    operations = [
        migrations.AlterField(
            model_name="asset",
            name="mac_address",
            field=models.CharField(
                blank=True,
                max_length=17,
                validators=[
                    django.core.validators.RegexValidator(
                        "^([0-9A-F]{2}:){5}[0-9A-F]{2}$",
                        "Enter a MAC address of twelve hex digits, e.g. AA:BB:CC:DD:EE:FF.",
                    )
                ],
                verbose_name="MAC address",
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]

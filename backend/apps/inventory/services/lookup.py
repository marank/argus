"""Resolve a scanned code (inventory number, serial number, IMEI or EAN)."""

from django.db.models import Q

from apps.inventory.models import Asset
from apps.masterdata.models import AssetModel


def lookup_code(code: str) -> dict:
    code = code.strip()
    if not code:
        return {"kind": "none", "assets": [], "models": []}

    assets = list(
        Asset.objects.select_related("model__manufacturer", "model__category", "assigned_to").filter(
            Q(inventory_number__iexact=code)
            | Q(serial_number__iexact=code)
            | Q(imei=code)
            | Q(mac_address__iexact=code)
        )[:20]
    )
    models = list(
        AssetModel.objects.select_related("manufacturer", "category").filter(
            Q(ean=code) | Q(part_number__iexact=code)
        )[:20]
    )
    if len(assets) == 1 and not models:
        kind = "asset"
    elif len(models) == 1 and not assets:
        kind = "model"
    elif assets or models:
        kind = "multiple"
    else:
        kind = "none"
    return {"kind": kind, "assets": assets, "models": models}

from typing import Any

from apps.accounts.models import User
from apps.inventory.models import Asset, AssetEvent


def log_event(asset: Asset, kind: str, user: User | None = None, **fields: Any) -> AssetEvent:
    """Append an entry to the asset's life cycle log."""
    return AssetEvent.objects.create(asset=asset, kind=kind, performed_by=user, **fields)

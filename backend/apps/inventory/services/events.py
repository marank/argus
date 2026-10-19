from apps.inventory.models import Asset, AssetEvent


def log_event(asset: Asset, kind: str, user=None, **fields) -> AssetEvent:
    """Append an entry to the asset's life cycle log."""
    return AssetEvent.objects.create(asset=asset, kind=kind, performed_by=user, **fields)

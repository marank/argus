from typing import Any

from apps.accounts.models import User
from apps.activity.models import ActivityKind
from apps.activity.services import log as activity
from apps.inventory.models import Asset, AssetEvent, AssetEventKind

# Written to the activity log by the service of the problem report instead.
ISSUE_KINDS = (AssetEventKind.ISSUE_REPORTED, AssetEventKind.ISSUE_RESOLVED)


def log_event(asset: Asset, kind: str, user: User | None = None, **fields: Any) -> AssetEvent:
    """Append an entry to the asset's life cycle log.

    It goes into the activity log too, unless it belongs to a request: the request's
    step covers all of its devices in one row.
    """
    event = AssetEvent.objects.create(asset=asset, kind=kind, performed_by=user, **fields)
    if event.asset_request_id is None and kind not in ISSUE_KINDS:
        activity.log(
            ActivityKind(f"asset_{kind}"),
            asset.pk,
            activity.asset_label(asset),
            user,
            related_user_id=event.related_user_id,
            detail=event.description,
        )
    return event

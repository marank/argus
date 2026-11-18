"""The history of a request, written by the workflow as each step happens."""

from typing import TYPE_CHECKING

from apps.activity.models import ActivityKind
from apps.activity.services import log as activity
from apps.requests.models import AssetRequest, AssetRequestAllocation, AssetRequestEvent

if TYPE_CHECKING:
    from apps.accounts.models import User


def record(
    asset_request: AssetRequest, kind: str, user: User | None = None, **data: object
) -> AssetRequestEvent:
    """Note a step; ``data`` holds plain values (texts, dates as ISO strings).

    The step also goes into the activity log, once for all devices it covers.
    """
    event = AssetRequestEvent.objects.create(
        asset_request=asset_request,
        kind=kind,
        actor=user if getattr(user, "pk", None) else None,
        data={key: value for key, value in data.items() if value not in (None, "", [])},
    )
    items = data.get("items")
    activity.log(
        ActivityKind(f"request_{kind}"),
        asset_request.pk,
        activity.request_label(asset_request),
        user,
        related_user_id=asset_request.requester_id,
        quantity=len(items) if isinstance(items, list) and items else None,
        detail=str(data.get("comment") or data.get("notes") or ""),
    )
    return event


def allocation_label(allocation: AssetRequestAllocation) -> str:
    """What was allocated, readable on its own: "MDE-0001", "2× USB-C cable", "Seat: Office"."""
    if allocation.asset:
        return allocation.asset.inventory_number
    if allocation.consumable:
        return f"{allocation.quantity}× {allocation.consumable.model}"
    return str(allocation.model)

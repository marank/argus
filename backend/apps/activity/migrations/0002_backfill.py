"""Fills the activity log once from the history kept so far.

Each source keeps its own time and actor. Steps of a request are taken from the
request history only, so a hand-out stays one row however many devices it covered.
Device events one person wrote in the same moment are one step as well: a
replacement, a series, an assignment with its change of status.
Purchase orders kept no history: only their creation is known.
"""

from collections.abc import Iterator
from datetime import timedelta
from typing import Any

from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

BATCH = 1000
# Device events written for a request or a problem report, or never written at all.
SKIPPED_ASSET_KINDS = ("issue_reported", "issue_resolved", "reserved")
# Device events that only follow from another one in the same step, most telling first.
SIDE_EFFECT_KINDS = ("assigned", "returned", "status_changed")
# Parts of one step were written within this time of each other.
STEP_WINDOW = timedelta(seconds=2)
# Request steps a direct hand-out or quick assignment writes along with its creation.
WITHIN_CREATION = ("allocated", "handed_out")
ISSUE_STATUS_KINDS = {
    "open": "issue_reopened",
    "in_progress": "issue_in_progress",
    "resolved": "issue_resolved",
}


def _asset_label(asset: Any) -> str:
    return f"{asset.inventory_number} · {asset.model.manufacturer.name} {asset.model.name}"


def _order_label(order: Any) -> str:
    return f"{order.number} · {order.supplier.name}" if order.supplier_id else order.number


def _requests(apps: Apps) -> Iterator[dict[str, Any]]:
    events = (
        apps.get_model("requests", "AssetRequestEvent")
        .objects.exclude(kind="released")
        .select_related("asset_request")
        .order_by("asset_request_id", "at", "pk")
    )
    held: dict[str, Any] | None = None
    for event in events.iterator(chunk_size=BATCH):
        request, data = event.asset_request, event.data or {}
        items = data.get("items")
        count = len(items) if isinstance(items, list) else 0
        # A direct hand-out or quick assignment and the devices it took at once: one row.
        if (
            held is not None
            and held["subject_id"] == request.pk
            and held["actor_id"] == event.actor_id
            and event.kind in WITHIN_CREATION
            and event.at - held["occurred_at"] <= STEP_WINDOW
        ):
            held["quantity"] = (held["quantity"] or 0) + count or None
            continue
        if held is not None:
            yield held
            held = None
        row = {
            "occurred_at": event.at,
            "actor_id": event.actor_id,
            "area": "requests",
            "kind": f"request_{event.kind}",
            "subject_id": request.pk,
            "subject_label": f"{request.number} – {request.title}",
            "related_user_id": request.requester_id,
            "quantity": count or None,
            "detail": str(data.get("comment") or data.get("notes") or ""),
        }
        if event.kind in ("direct", "quick"):
            held = row
        else:
            yield row
    if held is not None:
        yield held


def _asset_row(event: Any, kind: str | None = None, **fields: Any) -> dict[str, Any]:
    return {
        "occurred_at": event.created_at,
        "actor_id": event.performed_by_id,
        "area": "assets",
        "kind": kind or f"asset_{event.kind}",
        "subject_id": event.asset_id,
        "subject_label": _asset_label(event.asset),
        "related_user_id": event.related_user_id,
        "quantity": None,
        "detail": event.description,
        **fields,
    }


def _steps(events: Iterator[Any]) -> Iterator[list[Any]]:
    """Events one person wrote in the same moment: the parts of one step."""
    step: list[Any] = []
    for event in events:
        if step and (
            event.performed_by_id != step[0].performed_by_id
            or event.created_at - step[0].created_at > STEP_WINDOW
        ):
            yield step
            step = []
        step.append(event)
    if step:
        yield step


def _step_rows(step: list[Any]) -> Iterator[dict[str, Any]]:
    """One row per step, the way the log writes it today."""
    replaced = [e for e in step if e.kind == "replaced"]
    if replaced:
        # The replacement's entry comes last; it takes over the holder.
        replacement = replaced[-1]
        holder = next(
            (e.related_user_id for e in step if e.kind == "assigned" and e.asset_id == replacement.asset_id),
            None,
        )
        yield _asset_row(replacement, related_user_id=holder)
        return
    # Devices booked in from an order: the order's delivery.
    received: dict[Any, list[Any]] = {}
    for event in step:
        if event.kind == "created" and event.asset.purchase_order_line_id:
            received.setdefault(event.asset.purchase_order_line.order, []).append(event)
    for order, events in received.items():
        yield _asset_row(
            events[0],
            "order_received",
            area="procurement",
            subject_id=order.pk,
            subject_label=_order_label(order),
            related_user_id=None,
            quantity=len(events),
            detail="",
        )
    booked = {e.pk for events in received.values() for e in events}
    step = [e for e in step if e.pk not in booked]
    created = [e for e in step if e.kind == "created"]
    if len(created) > 1:
        first, last = created[0].asset, created[-1].asset
        names = dict.fromkeys(f"{e.asset.model.manufacturer.name} {e.asset.model.name}" for e in created)
        yield _asset_row(
            created[0],
            "assets_created",
            subject_id=None,
            subject_label=", ".join(names),
            quantity=len(created),
            detail=f"{first.inventory_number} – {last.inventory_number}",
        )
        step = [e for e in step if e.kind != "created"]
    for asset_id in dict.fromkeys(e.asset_id for e in step):
        events = [e for e in step if e.asset_id == asset_id]
        own = [e for e in events if e.kind not in SIDE_EFFECT_KINDS]
        if own:
            yield from (_asset_row(e) for e in own)
        else:
            yield _asset_row(min(events, key=lambda e: SIDE_EFFECT_KINDS.index(e.kind)))


def _assets(apps: Apps) -> Iterator[dict[str, Any]]:
    events = (
        apps.get_model("inventory", "AssetEvent")
        .objects.filter(asset_request__isnull=True)
        .exclude(kind__in=SKIPPED_ASSET_KINDS)
        .select_related("asset__model__manufacturer", "asset__purchase_order_line__order__supplier")
        .order_by("performed_by_id", "created_at", "pk")
    )
    for step in _steps(events.iterator(chunk_size=BATCH)):
        yield from _step_rows(step)


def _issues(apps: Apps) -> Iterator[dict[str, Any]]:
    issues = apps.get_model("inventory", "AssetIssue").objects.select_related("asset__model__manufacturer")
    for issue in issues.iterator(chunk_size=BATCH):
        yield {
            "occurred_at": issue.created_at,
            "actor_id": issue.reported_by_id,
            "area": "issues",
            "kind": "issue_reported",
            "subject_id": issue.pk,
            "subject_label": _asset_label(issue.asset),
            "related_user_id": issue.reported_by_id,
            "quantity": None,
            "detail": issue.description,
        }
    entries = (
        apps.get_model("inventory", "AssetIssueEntry")
        .objects.filter(kind="status", status__in=ISSUE_STATUS_KINDS)
        .select_related("issue__asset__model__manufacturer")
    )
    for entry in entries.iterator(chunk_size=BATCH):
        yield {
            "occurred_at": entry.created_at,
            "actor_id": entry.author_id,
            "area": "issues",
            "kind": ISSUE_STATUS_KINDS[entry.status],
            "subject_id": entry.issue_id,
            "subject_label": _asset_label(entry.issue.asset),
            "related_user_id": entry.issue.reported_by_id,
            "quantity": None,
            "detail": "",
        }


def _consumables(apps: Apps) -> Iterator[dict[str, Any]]:
    movements = (
        apps.get_model("inventory", "ConsumableMovement")
        .objects.filter(asset_request__isnull=True, purchase_order_line__isnull=True)
        # Used up in a repair: part of the device's service entry.
        .exclude(reason="consumption")
        .select_related("consumable__model__manufacturer", "consumable__location")
    )
    for movement in movements.iterator(chunk_size=BATCH):
        consumable = movement.consumable
        yield {
            "occurred_at": movement.created_at,
            "actor_id": movement.performed_by_id,
            "area": "consumables",
            "kind": f"consumable_{movement.reason}",
            "subject_id": consumable.pk,
            "subject_label": f"{consumable.model.manufacturer.name} {consumable.model.name}"
            f" · {consumable.location.name}",
            "related_user_id": movement.recipient_id,
            "quantity": movement.delta,
            "detail": movement.note,
        }


def _orders(apps: Apps) -> Iterator[dict[str, Any]]:
    orders = apps.get_model("procurement", "PurchaseOrder").objects.select_related("supplier")
    for order in orders.iterator(chunk_size=BATCH):
        yield {
            "occurred_at": order.created_at,
            "actor_id": order.created_by_id,
            "area": "procurement",
            "kind": "order_created",
            "subject_id": order.pk,
            "subject_label": _order_label(order),
            "related_user_id": None,
            "quantity": order.lines.count(),
            "detail": "",
        }


def backfill(apps: Apps, schema_editor: BaseDatabaseSchemaEditor | None) -> None:
    activity = apps.get_model("activity", "Activity")
    rows: list[Any] = []
    for source in (_requests, _assets, _issues, _consumables, _orders):
        for row in source(apps):
            row["subject_label"] = row["subject_label"][:300]
            rows.append(activity(**row))
            if len(rows) == BATCH:
                activity.objects.bulk_create(rows)
                rows = []
    activity.objects.bulk_create(rows)


def clear(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    apps.get_model("activity", "Activity").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0001_initial"),
        ("inventory", "0007_device_name_and_replacement"),
        ("procurement", "0002_uuid7_ids"),
        ("requests", "0003_devices_unrecorded"),
    ]

    operations = [migrations.RunPython(backfill, clear)]

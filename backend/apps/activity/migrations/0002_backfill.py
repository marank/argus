"""Fills the activity log once from the history kept so far.

Each source keeps its own time and actor. Steps of a request are taken from the
request history only, so a hand-out stays one row however many devices it covered.
Purchase orders kept no history: only their creation is known.
"""

from collections.abc import Iterator
from typing import Any

from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

BATCH = 1000
# Device events written for a request or a problem report, or never written at all.
SKIPPED_ASSET_KINDS = ("issue_reported", "issue_resolved", "reserved")
ISSUE_STATUS_KINDS = {
    "open": "issue_reopened",
    "in_progress": "issue_in_progress",
    "resolved": "issue_resolved",
}


def _asset_label(asset: Any) -> str:
    return f"{asset.inventory_number} · {asset.model.manufacturer.name} {asset.model.name}"


def _requests(apps: Apps) -> Iterator[dict[str, Any]]:
    events = apps.get_model("requests", "AssetRequestEvent").objects.exclude(kind="released")
    for event in events.select_related("asset_request").iterator(chunk_size=BATCH):
        request, data = event.asset_request, event.data or {}
        items = data.get("items")
        yield {
            "occurred_at": event.at,
            "actor_id": event.actor_id,
            "area": "requests",
            "kind": f"request_{event.kind}",
            "subject_id": request.pk,
            "subject_label": f"{request.number} – {request.title}",
            "related_user_id": request.requester_id,
            "quantity": len(items) if isinstance(items, list) and items else None,
            "detail": str(data.get("comment") or data.get("notes") or ""),
        }


def _assets(apps: Apps) -> Iterator[dict[str, Any]]:
    events = (
        apps.get_model("inventory", "AssetEvent")
        .objects.filter(asset_request__isnull=True)
        .exclude(kind__in=SKIPPED_ASSET_KINDS)
        .select_related("asset__model__manufacturer")
    )
    for event in events.iterator(chunk_size=BATCH):
        yield {
            "occurred_at": event.created_at,
            "actor_id": event.performed_by_id,
            "area": "assets",
            "kind": f"asset_{event.kind}",
            "subject_id": event.asset_id,
            "subject_label": _asset_label(event.asset),
            "related_user_id": event.related_user_id,
            "quantity": None,
            "detail": event.description,
        }


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
            "subject_label": f"{order.number} · {order.supplier.name}" if order.supplier_id else order.number,
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

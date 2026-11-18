"""The history kept so far goes into the log once."""

from importlib import import_module

from django.apps import apps

from apps.activity.models import Activity
from apps.inventory.models import AssetEvent, AssetIssue, ConsumableMovement
from apps.procurement.models import PurchaseOrder
from apps.requests.models import AssetRequestEvent

backfill = import_module("apps.activity.migrations.0002_backfill")


def test_backfill_takes_each_step_once(fresh):
    backfill.backfill(apps, None)

    request_events = AssetRequestEvent.objects.exclude(kind="released")
    assert Activity.objects.filter(area="requests").count() == request_events.count() > 0
    device_events = AssetEvent.objects.filter(asset_request__isnull=True).exclude(
        kind__in=backfill.SKIPPED_ASSET_KINDS
    )
    assert Activity.objects.filter(area="assets").count() == device_events.count() > 0
    stock = ConsumableMovement.objects.filter(asset_request__isnull=True, purchase_order_line__isnull=True)
    assert Activity.objects.filter(area="consumables").count() == stock.count()
    assert Activity.objects.filter(kind="issue_reported").count() == AssetIssue.objects.count()
    assert Activity.objects.filter(kind="order_created").count() == PurchaseOrder.objects.count()

    step = AssetRequestEvent.objects.select_related("asset_request").first()
    assert step is not None
    row = Activity.objects.get(
        kind=f"request_{step.kind}", subject_id=step.asset_request_id, occurred_at=step.at
    )
    assert row.subject_label == f"{step.asset_request.number} – {step.asset_request.title}"
    assert row.actor_id == step.actor_id

    backfill.clear(apps, None)
    assert not Activity.objects.exists()

"""The history kept so far goes into the log once."""

from datetime import timedelta
from importlib import import_module
from uuid import UUID

from django.apps import apps
from django.utils import timezone

from apps.accounts.models import User
from apps.activity.models import Activity
from apps.activity.tests.test_procurement import order
from apps.inventory.models import Asset, AssetEvent, AssetIssue, AssetStatus, ConsumableMovement
from apps.masterdata.models import AssetModel
from apps.procurement.models import PurchaseOrder, PurchaseOrderLine
from apps.requests.models import AssetRequestEvent

backfill = import_module("apps.activity.migrations.0002_backfill")


def test_backfill_takes_each_step_once(fresh):
    backfill.backfill(apps, None)

    request_events = AssetRequestEvent.objects.exclude(kind="released")
    assert 0 < Activity.objects.filter(area="requests").count() <= request_events.count()
    device_events = AssetEvent.objects.filter(asset_request__isnull=True).exclude(
        kind__in=backfill.SKIPPED_ASSET_KINDS
    )
    assert 0 < Activity.objects.filter(area="assets").count() <= device_events.count()
    stock = ConsumableMovement.objects.filter(
        asset_request__isnull=True, purchase_order_line__isnull=True
    ).exclude(reason="consumption")
    assert Activity.objects.filter(area="consumables").count() == stock.count()
    assert Activity.objects.filter(kind="issue_reported").count() == AssetIssue.objects.count()
    assert Activity.objects.filter(kind="order_created").count() == PurchaseOrder.objects.count()

    step = (
        AssetRequestEvent.objects.exclude(kind__in=("released", *backfill.WITHIN_CREATION))
        .select_related("asset_request")
        .first()
    )
    assert step is not None
    row = Activity.objects.get(
        kind=f"request_{step.kind}", subject_id=step.asset_request_id, occurred_at=step.at
    )
    assert row.subject_label == f"{step.asset_request.number} – {step.asset_request.title}"
    assert row.actor_id == step.actor_id

    backfill.clear(apps, None)
    assert not Activity.objects.exists()


def test_backfill_makes_one_row_of_each_device_step(it_client, fresh):
    AssetEvent.objects.all().delete()
    it, admin, employee = (User.objects.get(username=name) for name in ("it", "admin", "employee"))
    old, new, lent, first, second, *delivered = Asset.objects.order_by("inventory_number")[:7]
    pk = order(it_client, AssetModel.objects.get(name="SX58"), 2)
    line = PurchaseOrderLine.objects.select_related("order").get(order_id=UUID(pk))
    Asset.objects.filter(pk__in=[a.pk for a in delivered]).update(purchase_order_line=line)
    start = timezone.now() - timedelta(days=1)

    def event(asset, kind, seconds, by=it, **fields):
        created = AssetEvent.objects.create(asset=asset, kind=kind, performed_by=by, **fields)
        AssetEvent.objects.filter(pk=created.pk).update(created_at=start + timedelta(seconds=seconds))

    # A replacement wrote six events at once.
    event(old, "status_changed", 0)
    event(old, "returned", 0, related_user=employee)
    event(new, "status_changed", 0)
    event(new, "assigned", 0, related_user=employee)
    event(old, "replaced", 0, related_asset=new, description="Replaced by new")
    event(new, "replaced", 1, related_asset=old, description="Replaces old")
    # Someone else at the same moment is a step of their own.
    event(lent, "note", 1, by=admin, description="Scratch")
    # An assignment and its change of status.
    event(lent, "status_changed", 60)
    event(lent, "assigned", 60, related_user=employee)
    # A series.
    event(first, "created", 120)
    event(second, "created", 120)
    # Devices booked in from an order are its delivery.
    for asset in delivered:
        event(asset, "created", 180)

    backfill.backfill(apps, None)

    rows = Activity.objects.filter(area="assets").order_by("occurred_at", "kind")
    assert [(r.kind, r.subject_id, r.related_user_id, r.quantity) for r in rows] == [
        ("asset_note", lent.pk, None, None),
        ("asset_replaced", new.pk, employee.pk, None),
        ("asset_assigned", lent.pk, employee.pk, None),
        ("assets_created", None, None, 2),
    ]
    assert rows[1].detail == "Replaces old"
    assert rows[3].detail == f"{first.inventory_number} – {second.inventory_number}"
    delivery = Activity.objects.get(kind="order_received")
    assert (delivery.area, delivery.subject_id, delivery.quantity) == ("procurement", line.order_id, 2)
    assert delivery.subject_label == line.order.number


def test_backfill_makes_one_row_of_a_quick_assignment(it_client, fresh):
    asset = Asset.objects.filter(status=AssetStatus.IN_STOCK).order_by("inventory_number").first()
    assert asset is not None
    employee = User.objects.get(username="employee")
    response = it_client.post(
        "/api/requests/quick",
        {"asset": str(asset.pk), "requester": str(employee.pk), "duration": "permanent"},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    # The history has a step for the assignment and one for its hand-out.
    assert AssetRequestEvent.objects.filter(asset_request_id=response.json()["id"]).count() == 2
    Activity.objects.all().delete()

    backfill.backfill(apps, None)

    rows = Activity.objects.filter(subject_id=response.json()["id"])
    assert [(r.kind, r.quantity) for r in rows] == [("request_quick", 1)]

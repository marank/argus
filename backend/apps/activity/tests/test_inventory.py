"""Devices, stock, licenses and problem reports in the activity log."""

from apps.accounts.models import User
from apps.activity.models import Activity
from apps.inventory.models import Asset, AssetIssueStatus, AssetStatus, Consumable
from apps.inventory.services import assets as asset_service
from apps.inventory.services import issues
from apps.inventory.tests.test_asset_import import IMPORT, ROWS
from apps.masterdata.models import AssetModel, Location

JSON = "application/json"


def kinds() -> list[str]:
    return list(Activity.objects.order_by("occurred_at", "id").values_list("kind", flat=True))


def test_devices_created_together_are_one_row(it_client, fresh):
    sx58 = AssetModel.objects.get(name="SX58")
    warehouse = Location.objects.get(code="WH")
    response = it_client.post(
        "/api/inventory/assets/series",
        {"model": str(sx58.pk), "count": 3, "location": str(warehouse.pk)},
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    row = Activity.objects.get()
    assert (row.kind, row.quantity, row.subject_id, row.subject_label) == (
        "assets_created",
        3,
        None,
        sx58.full_name,
    )

    done = it_client.post(
        IMPORT, {"rows": ROWS, "defaults": {"location": str(warehouse.pk)}}, content_type=JSON
    ).json()
    assert done["created"] == 2
    imported = Activity.objects.get(kind="assets_imported")
    assert imported.quantity == 2
    assert kinds() == ["assets_created", "assets_imported"]


def test_device_steps_without_a_request(it_client, fresh):
    asset = Asset.objects.filter(status=AssetStatus.IN_STOCK, assigned_to=None).first()
    assert asset is not None
    employee = User.objects.get(username="employee")
    url = f"/api/inventory/assets/{asset.pk}"
    asset_service.update_asset(asset, {"assigned_to": employee.pk}, User.objects.get(username="it"))
    note = it_client.post(
        f"{url}/events", {"kind": "note", "description": "Display scratched"}, content_type=JSON
    )
    assert note.status_code == 201, note.content

    assigned, noted = Activity.objects.order_by("occurred_at", "id")
    assert (assigned.kind, assigned.related_user_id, assigned.subject_id) == (
        "asset_assigned",
        employee.pk,
        asset.pk,
    )
    assert assigned.subject_label == f"{asset.inventory_number} · {asset.model.full_name}"
    assert (noted.kind, noted.detail) == ("asset_note", "Display scratched")


def test_deleted_device_keeps_its_label(it_client, fresh):
    asset = Asset.objects.create(model=AssetModel.objects.get(name="SX58"))
    label = f"{asset.inventory_number} · {asset.model.full_name}"
    assert it_client.delete(f"/api/inventory/assets/{asset.pk}").status_code == 204
    row = Activity.objects.get()
    assert (row.kind, row.subject_id, row.subject_label) == ("asset_deleted", None, label)


def test_stock_moved_by_hand(it_client, fresh):
    consumable = Consumable.objects.filter(quantity__gt=1).first()
    assert consumable is not None
    response = it_client.post(
        f"/api/inventory/consumables/{consumable.pk}/move",
        {"delta": -1, "reason": "issue", "note": "Desk 4"},
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    row = Activity.objects.get()
    assert (row.area, row.kind, row.quantity, row.detail) == ("consumables", "consumable_issue", -1, "Desk 4")


def test_problem_report_steps(demo, fresh):
    employee, it = User.objects.get(username="employee"), User.objects.get(username="it")
    asset = Asset.objects.filter(assigned_to=employee).first()
    assert asset is not None
    issue = issues.report_issue(asset, employee, "defect", "Does not boot")
    issues.update_issue(issue, it, AssetIssueStatus.IN_PROGRESS, by_it=True)
    issues.update_issue(issue, it, AssetIssueStatus.RESOLVED, "New battery", by_it=True)
    issues.update_issue(issue, it, AssetIssueStatus.OPEN, by_it=True)

    assert kinds() == ["issue_reported", "issue_in_progress", "issue_resolved", "issue_reopened"]
    assert set(Activity.objects.values_list("area", "subject_id")) == {("issues", issue.pk)}
    assert Activity.objects.get(kind="issue_resolved").detail == "New battery"


def test_license_steps(it_client, fresh):
    acrobat = AssetModel.objects.get(name="Acrobat Pro")
    created = it_client.post(
        "/api/inventory/licenses",
        {"model": str(acrobat.pk), "seats": 2, "assign_to": "user"},
        content_type=JSON,
    ).json()
    url = f"/api/inventory/licenses/{created['id']}"
    employee = User.objects.get(username="employee")
    seats = it_client.post(f"{url}/assignments", {"user": str(employee.pk)}, content_type=JSON).json()
    seat = seats["assignments"][0]["id"]
    assert it_client.delete(f"{url}/assignments/{seat}").status_code == 200
    assert it_client.delete(url).status_code == 204

    assert kinds() == ["license_created", "license_assigned", "license_unassigned", "license_deleted"]
    assert Activity.objects.get(kind="license_assigned").related_user_id == employee.pk

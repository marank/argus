from apps.inventory.models import Asset, AssetEvent

JSON = "application/json"


def own_device():
    return Asset.objects.filter(assigned_to__username="employee").order_by("inventory_number").first()


def test_employee_reports_problem_and_it_resolves_it(employee_client, it_client):
    asset = own_device()
    response = employee_client.post(
        f"/api/portal/my-assets/{asset.pk}/issues",
        {"kind": "defect", "description": "Display flickers"},
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    issue_id = response.json()["id"]

    # The employee sees the open report on the device.
    devices = {d["id"]: d for d in employee_client.get("/api/portal/my-assets").json()}
    assert [i["status"] for i in devices[str(asset.pk)]["issues"]] == ["open"]

    # IT sees it in the list, on the dashboard and in the device history.
    issues = it_client.get("/api/inventory/issues?status=open&status=in_progress").json()["items"]
    assert [i["id"] for i in issues] == [issue_id]
    assert issues[0]["reported_by"]["username"] == "employee"
    assert it_client.get("/api/dashboard/it").json()["open_issues"] == 1
    assert AssetEvent.objects.filter(asset=asset, kind="issue_reported").exists()
    assert [i["id"] for i in it_client.get(f"/api/inventory/assets/{asset.pk}").json()["open_issues"]] == [
        issue_id
    ]

    # Resolving needs a note for the employee.
    response = it_client.put(f"/api/inventory/issues/{issue_id}", {"status": "resolved"}, content_type=JSON)
    assert response.status_code == 409
    response = it_client.put(
        f"/api/inventory/issues/{issue_id}",
        {"status": "resolved", "resolution": "Display replaced"},
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    assert response.json()["handled_by"]["username"] == "it"
    assert it_client.get("/api/dashboard/it").json()["open_issues"] == 0
    assert AssetEvent.objects.filter(asset=asset, kind="issue_resolved").exists()

    # The answer stays visible to the employee for a while.
    devices = {d["id"]: d for d in employee_client.get("/api/portal/my-assets").json()}
    assert devices[str(asset.pk)]["issues"][0]["resolution"] == "Display replaced"


def test_only_own_devices_can_be_reported(employee_client):
    foreign = Asset.objects.exclude(assigned_to__username="employee").first()
    response = employee_client.post(
        f"/api/portal/my-assets/{foreign.pk}/issues",
        {"kind": "other", "description": "Not mine"},
        content_type=JSON,
    )
    assert response.status_code == 404


def test_report_needs_description(employee_client):
    response = employee_client.post(
        f"/api/portal/my-assets/{own_device().pk}/issues",
        {"kind": "damage", "description": "   "},
        content_type=JSON,
    )
    assert response.status_code == 409


def test_employees_cannot_list_all_reports(employee_client):
    assert employee_client.get("/api/inventory/issues").status_code in (401, 403)


def test_device_detail_shows_all_reports(employee_client):
    asset = own_device()
    employee_client.post(
        f"/api/portal/my-assets/{asset.pk}/issues",
        {"kind": "damage", "description": "Hinge broken"},
        content_type=JSON,
    )
    detail = employee_client.get(f"/api/portal/my-assets/{asset.pk}")
    assert detail.status_code == 200, detail.content
    assert [i["description"] for i in detail.json()["issues"]] == ["Hinge broken"]

    foreign = Asset.objects.exclude(assigned_to__username="employee").first()
    assert employee_client.get(f"/api/portal/my-assets/{foreign.pk}").status_code == 404
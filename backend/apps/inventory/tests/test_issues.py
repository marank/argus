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

    # IT resolves it and tells the employee what was done.
    response = it_client.put(
        f"/api/inventory/issues/{issue_id}",
        {"status": "resolved", "message": "Display replaced"},
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    assert response.json()["handled_by"]["username"] == "it"
    assert it_client.get("/api/dashboard/it").json()["open_issues"] == 0
    assert AssetEvent.objects.filter(asset=asset, kind="issue_resolved").exists()

    # The employee sees IT's answer in the conversation.
    entries = employee_client.get(f"/api/portal/my-issues/{issue_id}").json()["entries"]
    assert [(e["kind"], e["side"], e["text"] or e["status"]) for e in entries] == [
        ("message", "it", "Display replaced"),
        ("status", "it", "resolved"),
    ]


def test_only_own_devices_can_be_reported(employee_client):
    foreign = Asset.objects.exclude(assigned_to__username="employee").first()
    assert foreign is not None
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
    assert foreign is not None
    assert employee_client.get(f"/api/portal/my-assets/{foreign.pk}").status_code == 404


def test_my_issues_lists_own_reports(employee_client, it_client):
    asset = own_device()
    employee_client.post(
        f"/api/portal/my-assets/{asset.pk}/issues",
        {"kind": "lost", "description": "Left in the train"},
        content_type=JSON,
    )
    issues = employee_client.get("/api/portal/my-issues").json()
    assert [(i["description"], i["still_assigned"]) for i in issues] == [("Left in the train", True)]
    assert issues[0]["asset"]["inventory_number"] == asset.inventory_number

    # Other employees' reports are not listed.
    assert it_client.get("/api/portal/my-issues").json() == []


def report(client) -> str:
    response = client.post(
        f"/api/portal/my-assets/{own_device().pk}/issues",
        {"kind": "defect", "description": "Fan is loud"},
        content_type=JSON,
    )
    return response.json()["id"]


def test_both_sides_write_messages_at_any_time(employee_client, it_client):
    issue_id = report(employee_client)
    it_url = f"/api/inventory/issues/{issue_id}"
    own_url = f"/api/portal/my-issues/{issue_id}"

    response = it_client.post(f"{it_url}/messages", {"text": "Since when?"}, content_type=JSON)
    assert response.status_code == 200, response.content
    # News for the employee until they open the report.
    assert employee_client.get("/api/portal/menu-counts").json()["issues_updated"] is True
    detail = employee_client.get(own_url).json()
    assert detail["unseen_update"] is True
    assert employee_client.get("/api/portal/menu-counts").json()["issues_updated"] is False

    response = employee_client.post(f"{own_url}/messages", {"text": "Since Monday"}, content_type=JSON)
    assert response.status_code == 200, response.content
    entries = it_client.get(it_url).json()["entries"]
    assert [(e["side"], e["author"]["username"], e["text"]) for e in entries] == [
        ("it", "it", "Since when?"),
        ("reporter", "employee", "Since Monday"),
    ]
    # Writing does not change the status, and empty messages are refused.
    assert it_client.get(it_url).json()["status"] == "open"
    assert employee_client.post(f"{own_url}/messages", {"text": "  "}, content_type=JSON).status_code == 409

    # Still possible once resolved.
    it_client.put(it_url, {"status": "resolved"}, content_type=JSON)
    response = employee_client.post(f"{own_url}/messages", {"text": "Thanks!"}, content_type=JSON)
    assert response.status_code == 200, response.content


def test_reporter_marks_resolved_but_cannot_reopen(employee_client, it_client):
    issue_id = report(employee_client)
    own_url = f"/api/portal/my-issues/{issue_id}"
    response = employee_client.post(f"{own_url}/resolve", {"text": "Was the power plug"}, content_type=JSON)
    assert response.status_code == 200, response.content
    detail = response.json()
    assert detail["status"] == "resolved"
    assert [(e["kind"], e["side"]) for e in detail["entries"]] == [
        ("message", "reporter"),
        ("status", "reporter"),
    ]
    # Their own action is no news to them; IT is not recorded as handling it.
    assert detail["unseen_update"] is False
    assert detail["handled_by"] is None
    assert employee_client.post(f"{own_url}/resolve", {}, content_type=JSON).status_code == 409

    # Reopening is IT's call.
    response = it_client.put(f"/api/inventory/issues/{issue_id}", {"status": "open"}, content_type=JSON)
    assert response.status_code == 200, response.content


def test_detail_lists_other_reports_on_the_device(employee_client, it_client):
    first, second = report(employee_client), report(employee_client)
    others = employee_client.get(f"/api/portal/my-issues/{second}").json()["other_issues"]
    assert [i["id"] for i in others] == [first]
    detail = it_client.get(f"/api/inventory/issues/{second}").json()
    assert detail["reported_by"]["display_name"]
    assert detail["asset"]["inventory_number"] == own_device().inventory_number
    assert detail["still_assigned"] is True


def test_reports_of_others_stay_private(employee_client, it_client):
    from apps.accounts.models import User
    from apps.inventory.models import AssetIssue

    asset = Asset.objects.first()
    assert asset is not None
    foreign = AssetIssue.objects.create(
        asset=asset, description="Not yours", reported_by=User.objects.get(username="it")
    )
    assert employee_client.get(f"/api/portal/my-issues/{foreign.pk}").status_code == 404
    url = f"/api/portal/my-issues/{foreign.pk}/messages"
    assert employee_client.post(url, {"text": "Hi"}, content_type=JSON).status_code == 404
    assert employee_client.get(f"/api/inventory/issues/{foreign.pk}").status_code == 403


def test_reporter_does_not_see_who_has_the_device_now(employee_client, it_client):
    from apps.accounts.models import Team, User
    from apps.inventory.models import AssetIssue

    asset = own_device()
    issue_id = report(employee_client)
    own_url = f"/api/portal/my-issues/{issue_id}"
    employee = User.objects.get(username="employee")
    # While the device is theirs, the reporter sees themselves as its holder.
    assert employee_client.get(own_url).json()["asset"]["assigned_to"]["id"] == str(employee.pk)

    sales = User.objects.get(username="sales")
    Asset.objects.filter(pk=asset.pk).update(assigned_to=sales)
    team = Team.objects.create(name="Second level", code="2ND")
    AssetIssue.objects.filter(pk=issue_id).update(
        assigned_team=team, assignee=User.objects.get(username="it")
    )

    body = employee_client.get(own_url).json()
    assert body["asset"]["assigned_to"] is None and body["asset"]["assigned_since"] is None
    assert body["assigned_team"] is None and body["assignee"] is None
    assert "Seller" not in str(body)

    body = it_client.get(f"/api/inventory/issues/{issue_id}").json()
    assert body["asset"]["assigned_to"]["id"] == str(sales.pk)
    assert body["assigned_team"]["id"] == str(team.pk)
    assert body["assignee"]["username"] == "it"

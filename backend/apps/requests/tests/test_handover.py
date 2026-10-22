from apps.accounts.models import User
from apps.inventory.models import Asset, AssetEvent
from apps.requests.models import AssetRequest, Handover

# 1×1 PNG
SIGNATURE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def ready_pickup() -> AssetRequest:
    return AssetRequest.objects.get(status=AssetRequest.Status.READY, handover_mode="pickup")


def test_terminal_lists_and_signs_pickup(terminal_client):
    asset_request = ready_pickup()
    listed = terminal_client.get("/api/terminal/pickups").json()
    assert [p["id"] for p in listed] == [str(asset_request.pk)]

    detail = terminal_client.get(f"/api/terminal/pickups/{asset_request.pk}").json()
    allocation = detail["items"][0]["allocations"][0]

    response = terminal_client.post(
        f"/api/terminal/pickups/{asset_request.pk}/sign",
        {
            "received_by_name": "Max Colleague",
            "signature": SIGNATURE,
            "notes": "Collected on behalf of Sam",
            "allocation_notes": [{"allocation": allocation["id"], "note": "Scratch on lid"}],
        },
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["status"] == "completed"  # permanent request
    assert body["handover"]["method"] == "signature"
    assert body["handover"]["received_by_name"] == "Max Colleague"

    asset = Asset.objects.get(pk=allocation["asset"]["id"])
    assert asset.assigned_to == asset_request.requester  # devices belong to the requester
    event = asset.events.filter(kind=AssetEvent.Kind.ASSIGNED).first()
    assert event.description == "Scratch on lid"
    assert terminal_client.get("/api/terminal/pickups").json() == []


def test_signature_is_required(terminal_client):
    asset_request = ready_pickup()
    response = terminal_client.post(
        f"/api/terminal/pickups/{asset_request.pk}/sign",
        {"signature": ""},
        content_type="application/json",
    )
    assert response.status_code == 409
    assert not Handover.objects.exists()


def test_terminal_account_is_confined(terminal_client):
    assert terminal_client.get("/api/auth/me").status_code == 200
    assert terminal_client.get("/api/requests").status_code == 403
    assert terminal_client.get("/api/inventory/assets").status_code == 403


def test_employee_cannot_use_terminal(employee_client):
    assert employee_client.get("/api/terminal/pickups").status_code == 403


def test_delivered_by_it(it_client):
    asset_request = ready_pickup()
    response = it_client.post(
        f"/api/requests/{asset_request.pk}/hand-out",
        {"method": "delivered", "location": "Sales office 2.14", "notes": "Placed on desk"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    handover = response.json()["handover"]
    assert handover["method"] == "delivered"
    assert handover["received_by_name"] == asset_request.requester.display_name
    assert handover["location"] == "Sales office 2.14"
    assert handover["signature"] == ""


def test_terminal_finds_people_by_name_words_and_number(terminal_client):
    employee = User.objects.get(username="employee")
    employee.employee_number = "4711"
    employee.save()

    def names(q):
        return {p["display_name"] for p in terminal_client.get("/api/terminal/people", {"q": q}).json()}

    assert employee.display_name in names("4711")
    assert names(f"{employee.first_name} {employee.last_name[:3]}") == {employee.display_name}
    assert names("47") == set()  # numbers only match in full

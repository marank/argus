"""Requests handed out outside the system, before IT prepared them."""

from django.core import mail

from apps.accounts.models import User
from apps.inventory.models import Asset, AssetEventKind, AssetStatus
from apps.requests.models import AssetRequest, AssetRequestEventKind, AssetRequestStatus

from .flow import JSON, laptops, submit


def confirmed(employee_client, it_client, duration="temporary", quantity=1) -> str:
    items = [{**laptops()[0], "quantity": quantity}]
    response = submit(employee_client, items, duration)
    assert response.status_code == 201, response.content
    rid: str = response.json()["id"]
    response = it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)
    assert response.status_code == 200, response.content
    return rid


def spare_laptops() -> list[Asset]:
    return list(
        Asset.objects.filter(model__category__code="laptops", status=AssetStatus.IN_STOCK).order_by(
            "inventory_number"
        )
    )


def record_device(it_client, rid: str, asset: Asset):
    item = AssetRequest.objects.get(pk=rid).items.get()
    return it_client.post(
        f"/api/requests/{rid}/allocations", {"item": str(item.pk), "asset": str(asset.pk)}, content_type=JSON
    )


def hand_out_unrecorded(it_client, rid: str, notes: str = ""):
    return it_client.post(f"/api/requests/{rid}/hand-out-unrecorded", {"notes": notes}, content_type=JSON)


def test_hand_out_without_devices_waits_for_the_return(employee_client, it_client):
    rid = confirmed(employee_client, it_client)
    sent = len(mail.outbox)

    response = hand_out_unrecorded(it_client, rid, "Given at the desk")
    assert response.status_code == 200, response.content
    body = response.json()
    assert (body["status"], body["devices_unrecorded"]) == ("handed_out", True)
    assert body["handed_out_at"]
    assert body["handover"]["notes"] == "Given at the desk"
    assert body["items"][0]["quantity_missing"] == 1
    handed = next(e for e in body["events"] if e["kind"] == "handed_out")
    assert handed["data"]["missing"] == ["1× Laptops"]
    # The employee already has the devices: no message about it.
    assert len(mail.outbox) == sent


def test_device_recorded_later_counts_as_handed_out_then(employee_client, it_client):
    rid = confirmed(employee_client, it_client)
    hand_out_unrecorded(it_client, rid)
    asset_request = AssetRequest.objects.get(pk=rid)
    laptop = spare_laptops()[0]

    response = record_device(it_client, rid, laptop)
    assert response.status_code == 200, response.content
    body = response.json()
    assert (body["status"], body["devices_unrecorded"]) == ("handed_out", False)
    laptop.refresh_from_db()
    assert (laptop.status, laptop.assigned_to, laptop.assigned_since) == (
        AssetStatus.IN_USE,
        asset_request.requester,
        asset_request.handed_out_at,
    )
    assert laptop.events.filter(kind=AssetEventKind.ASSIGNED, asset_request=asset_request).exists()
    allocation = asset_request.items.get().allocations.get()
    assert allocation.handed_out_at == asset_request.handed_out_at
    assert asset_request.events.filter(
        kind=AssetRequestEventKind.ALLOCATED, data__items=[laptop.inventory_number]
    ).exists()

    # From now on it is an ordinary loan.
    response = it_client.post(f"/api/requests/{rid}/return", {}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "completed"


def test_returned_without_devices_completes_the_request(employee_client, it_client):
    rid = confirmed(employee_client, it_client)
    hand_out_unrecorded(it_client, rid)

    response = it_client.post(
        f"/api/requests/{rid}/return-unrecorded", {"notes": "All back"}, content_type=JSON
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert (body["status"], body["devices_unrecorded"]) == ("completed", False)
    returned = next(e for e in body["events"] if e["kind"] == "returned")
    assert returned["data"] == {"items": [], "damaged": [], "notes": "All back", "missing": ["1× Laptops"]}

    # Nothing can be recorded for it any more.
    assert record_device(it_client, rid, spare_laptops()[0]).status_code >= 400


def test_recorded_devices_come_back_on_their_own(employee_client, it_client):
    rid = confirmed(employee_client, it_client, quantity=2)
    prepared = spare_laptops()[0]
    record_device(it_client, rid, prepared)

    hand_out_unrecorded(it_client, rid)
    prepared.refresh_from_db()
    assert prepared.status == AssetStatus.IN_USE
    asset_request = AssetRequest.objects.get(pk=rid)
    handed = asset_request.events.get(kind=AssetRequestEventKind.HANDED_OUT)
    assert (handed.data["items"], handed.data["missing"]) == ([prepared.inventory_number], ["1× Laptops"])

    # The recorded laptop is back, the other one is still out.
    response = it_client.post(f"/api/requests/{rid}/return", {}, content_type=JSON)
    assert response.json()["status"] == "handed_out"
    prepared.refresh_from_db()
    assert prepared.status == AssetStatus.IN_STOCK

    response = it_client.post(f"/api/requests/{rid}/return-unrecorded", {}, content_type=JSON)
    assert response.json()["status"] == "completed"


def test_return_without_devices_leaves_recorded_ones_out(employee_client, it_client):
    rid = confirmed(employee_client, it_client, quantity=2)
    hand_out_unrecorded(it_client, rid)
    laptop = spare_laptops()[0]
    record_device(it_client, rid, laptop)

    response = it_client.post(f"/api/requests/{rid}/return-unrecorded", {}, content_type=JSON)
    assert (response.json()["status"], response.json()["devices_unrecorded"]) == ("handed_out", False)
    response = it_client.post(f"/api/requests/{rid}/return", {}, content_type=JSON)
    assert response.json()["status"] == "completed"


def test_permanent_request_completes_and_devices_can_still_be_recorded(employee_client, it_client):
    rid = confirmed(employee_client, it_client, duration="permanent")
    body = hand_out_unrecorded(it_client, rid).json()
    assert (body["status"], body["devices_unrecorded"]) == ("completed", True)

    # Nothing is expected back.
    assert it_client.post(f"/api/requests/{rid}/return-unrecorded", {}, content_type=JSON).status_code >= 400

    laptop = spare_laptops()[0]
    body = record_device(it_client, rid, laptop).json()
    assert (body["status"], body["devices_unrecorded"]) == ("completed", False)
    laptop.refresh_from_db()
    assert laptop.assigned_to == User.objects.get(username="employee")


def test_hand_out_without_devices_only_for_confirmed_requests_missing_devices(employee_client, it_client):
    response = submit(employee_client, laptops())
    submitted = response.json()["id"]
    assert hand_out_unrecorded(it_client, submitted).status_code >= 400

    rid = confirmed(employee_client, it_client)
    record_device(it_client, rid, spare_laptops()[0])
    assert hand_out_unrecorded(it_client, rid).status_code >= 400
    assert AssetRequest.objects.get(pk=rid).status == AssetRequestStatus.CONFIRMED

    # Employees cannot do it.
    assert hand_out_unrecorded(employee_client, rid).status_code == 403


def test_return_without_devices_needs_unrecorded_devices(employee_client, it_client):
    rid = confirmed(employee_client, it_client)
    record_device(it_client, rid, spare_laptops()[0])
    it_client.post(
        f"/api/requests/{rid}/ready", {"handover_mode": "collect", "notify": False}, content_type=JSON
    )
    it_client.post(f"/api/requests/{rid}/hand-out", {"method": "direct"}, content_type=JSON)
    assert AssetRequest.objects.get(pk=rid).status == AssetRequestStatus.HANDED_OUT
    assert it_client.post(f"/api/requests/{rid}/return-unrecorded", {}, content_type=JSON).status_code >= 400

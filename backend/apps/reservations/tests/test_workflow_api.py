from datetime import date, datetime, timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Asset
from apps.masterdata.models import Category, Location


def test_full_reservation_cycle(employee_client, it_client):
    laptops = Category.objects.get(code="laptops")
    start = date.today() + timedelta(days=3)
    response = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=5)).isoformat(),
            "items": [{"category": laptops.pk, "quantity": 3}],
        },
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    reservation = response.json()
    item_id = reservation["items"][0]["id"]

    # IT approves only two laptops.
    response = it_client.post(
        f"/api/reservations/{reservation['id']}/approve",
        {"items": [{"id": item_id, "quantity_approved": 2}], "comment": "Only two left"},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "approved"

    # Not ready while devices are missing.
    response = it_client.post(
        f"/api/reservations/{reservation['id']}/ready", {}, content_type="application/json"
    )
    assert response.status_code == 409

    response = it_client.post(f"/api/reservations/{reservation['id']}/auto-allocate")
    assert response.json()["allocated"] == 2
    allocated = [a["asset"]["id"] for a in response.json()["reservation"]["items"][0]["allocations"]]
    assert set(Asset.objects.filter(pk__in=allocated).values_list("status", flat=True)) == {"reserved"}

    response = it_client.post(
        f"/api/reservations/{reservation['id']}/ready", {}, content_type="application/json"
    )
    assert response.status_code == 200
    response = it_client.post(
        f"/api/reservations/{reservation['id']}/hand-out", {}, content_type="application/json"
    )
    assert response.json()["status"] == "handed_out"

    my_assets = employee_client.get("/api/portal/my-assets").json()
    assert {a["id"] for a in my_assets} >= set(allocated)

    response = it_client.post(
        f"/api/reservations/{reservation['id']}/return", {}, content_type="application/json"
    )
    assert response.json()["status"] == "completed"
    assert set(Asset.objects.filter(pk__in=allocated).values_list("status", flat=True)) == {"in_stock"}


def test_employee_sees_only_own_reservations(employee_client, demo):
    from django.test import Client

    from apps.accounts.models import User

    User.objects.create_user("newbie", password="argus-demo")
    other = Client()
    other.login(username="newbie", password="argus-demo")
    assert other.get("/api/reservations").json()["count"] == 0
    assert employee_client.get("/api/reservations").json()["count"] == 3


def test_order_from_need_and_receive(it_client):
    needs = it_client.get("/api/procurement/needs").json()
    consumable_need = next(n for n in needs["consumables"] if n["to_order"] > 0)
    model_id = consumable_need["consumable"]["model"]["id"]
    response = it_client.post(
        "/api/procurement/orders",
        {"lines": [{"asset_model": model_id, "quantity": consumable_need["to_order"]}]},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    order = response.json()
    assert (
        it_client.post(
            f"/api/procurement/orders/{order['id']}/ordered", {}, content_type="application/json"
        ).json()["status"]
        == "ordered"
    )
    response = it_client.post(
        f"/api/procurement/orders/{order['id']}/receive",
        {
            "receipts": [
                {
                    "line": order["lines"][0]["id"],
                    "quantity": consumable_need["to_order"],
                    "location": consumable_need["consumable"]["location"]["id"],
                }
            ]
        },
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "received"


def test_lookup_by_ean_and_serial(it_client):
    asset = Asset.objects.first()
    result = it_client.get(f"/api/inventory/lookup?code={asset.serial_number}").json()
    assert result["kind"] == "asset"
    result = it_client.get(f"/api/inventory/lookup?code={asset.model.ean}").json()
    assert result["kind"] in {"model", "multiple"}


def test_catalog_hides_availability_from_employees(employee_client, it_client):
    employee_view = employee_client.get("/api/portal/catalog").json()
    assert employee_view and all(c["available"] is None for c in employee_view)
    assert all(m["available"] is None for c in employee_view for m in c["models"])

    it_view = it_client.get("/api/portal/catalog").json()
    assert any(c["available"] for c in it_view)


def _ready_request(employee_client, it_client, **ready) -> dict:
    headsets = Category.objects.get(code="headsets")
    start = date.today() + timedelta(days=2)
    reservation = employee_client.post(
        "/api/reservations",
        {
            "title": "Calls",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=2)).isoformat(),
            "items": [{"category": headsets.pk, "quantity": 1}],
        },
        content_type="application/json",
    ).json()
    item_id = reservation["items"][0]["id"]
    base = f"/api/reservations/{reservation['id']}"
    it_client.post(
        f"{base}/approve",
        {"items": [{"id": item_id, "quantity_approved": 1}]},
        content_type="application/json",
    )
    it_client.post(f"{base}/auto-allocate")
    response = it_client.post(f"{base}/ready", ready, content_type="application/json")
    assert response.status_code == 200, response.content
    return response.json()


def test_ready_can_skip_the_device_check(employee_client, it_client, terminal_client):
    reservation = _ready_request(employee_client, it_client, handover_mode="pickup", skip_device_check=True)
    assert reservation["skip_device_check"] is True
    pickup = terminal_client.get(f"/api/terminal/pickups/{reservation['id']}").json()
    assert pickup["skip_device_check"] is True


def test_ready_request_can_be_reopened(employee_client, it_client, terminal_client):
    reservation = _ready_request(employee_client, it_client, handover_mode="pickup")
    base = f"/api/reservations/{reservation['id']}"

    response = it_client.post(f"{base}/reopen")
    assert response.status_code == 200
    reopened = response.json()
    assert reopened["status"] == "approved"
    # Devices stay allocated; the terminal no longer offers the pickup.
    assert reopened["items"][0]["allocations"]
    assert terminal_client.get(f"/api/terminal/pickups/{reservation['id']}").status_code == 404
    # Only ready requests can be reopened.
    assert it_client.post(f"{base}/reopen").status_code == 409


def test_ready_confirms_date_and_place(employee_client, it_client):
    place = Location.objects.first()
    pickup = (timezone.now() + timedelta(days=3)).replace(microsecond=0)
    reservation = _ready_request(
        employee_client,
        it_client,
        handover_mode="pickup",
        pickup_at=pickup.isoformat(),
        pickup_location=str(place.pk),
    )
    assert reservation["status"] == "ready"
    assert reservation["pickup_location"]["id"] == str(place.pk)
    # Compare instants: the API answers in UTC, which is another day around local midnight.
    assert datetime.fromisoformat(reservation["pickup_at"]) == pickup


def test_simple_pickup_is_recorded_by_it(employee_client, it_client, terminal_client):
    reservation = _ready_request(employee_client, it_client, handover_mode="collect")
    # Not offered at the terminal: nobody signs.
    assert terminal_client.get(f"/api/terminal/pickups/{reservation['id']}").status_code == 404

    colleague = User.objects.get(username="sales")
    response = it_client.post(
        f"/api/reservations/{reservation['id']}/hand-out",
        {"method": "direct", "received_by": str(colleague.pk)},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["handover"]["received_by"]["id"] == str(colleague.pk)


def _request_with_pickup_wish(client, start: date, wish: date):
    return client.post(
        "/api/reservations",
        {
            "title": "Trip",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=2)).isoformat(),
            "requested_pickup_date": wish.isoformat(),
            "items": [{"category": Category.objects.get(code="headsets").pk, "quantity": 1}],
        },
        content_type="application/json",
    )


def test_employees_name_a_preferred_pickup_day(employee_client):
    start = date.today() + timedelta(days=5)
    response = _request_with_pickup_wish(employee_client, start, start - timedelta(days=1))
    assert response.status_code == 201, response.content
    assert response.json()["requested_pickup_date"] == (start - timedelta(days=1)).isoformat()
    assert response.json()["pickup_at"] is None  # the appointment is IT's decision

    # Not after the devices are needed, not in the past.
    assert _request_with_pickup_wish(employee_client, start, start + timedelta(days=1)).status_code == 409
    assert (
        _request_with_pickup_wish(employee_client, start, date.today() - timedelta(days=1)).status_code == 409
    )

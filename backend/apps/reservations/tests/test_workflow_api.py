from datetime import date, timedelta

from apps.inventory.models import Asset
from apps.masterdata.models import Category


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

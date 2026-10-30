from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Asset, AssetStatus, Consumable
from apps.requests.models import AssetRequest

URL = "/api/requests/direct"
JSON = "application/json"


def in_stock(count: int = 1) -> list[Asset]:
    assets = list(Asset.objects.filter(status=AssetStatus.IN_STOCK).order_by("inventory_number")[:count])
    assert len(assets) == count
    return assets


def stock() -> Consumable:
    return next(c for c in Consumable.objects.all() if c.available_quantity >= 2)


def employee() -> User:
    return User.objects.get(username="employee")


def post(client, **data):
    payload = {
        "title": "New colleague",
        "duration": "permanent",
        "start_date": str(timezone.localdate()),
        "requester": str(employee().pk),
        **data,
    }
    return client.post(URL, payload, content_type=JSON)


def test_confirms_and_allocates_specific_devices(it_client):
    first, second = in_stock(2)
    consumable = stock()
    response = post(
        it_client,
        assets=[str(first.pk), str(second.pk)],
        consumables=[{"consumable": str(consumable.pk), "quantity": 2}],
    )
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["origin"] == "direct"
    assert body["status"] == "confirmed"
    assert body["approval"] == ""
    assert body["requester"]["id"] == str(employee().pk)
    assert sum(item["quantity_allocated"] for item in body["items"]) == 4
    assert all(item["quantity_missing"] == 0 for item in body["items"])

    first.refresh_from_db()
    assert first.status == AssetStatus.RESERVED
    consumable.refresh_from_db()
    assert consumable.reserved_quantity == 2


def test_then_runs_like_any_request(it_client):
    (asset,) = in_stock()
    body = post(
        it_client,
        assets=[str(asset.pk)],
        duration="temporary",
        end_date=str(timezone.localdate() + timedelta(days=3)),
    ).json()
    url = f"/api/requests/{body['id']}"

    ready = it_client.post(f"{url}/ready", {"handover_mode": "collect"}, content_type=JSON)
    assert ready.status_code == 200, ready.content
    handed = it_client.post(f"{url}/hand-out", {}, content_type=JSON)
    assert handed.json()["status"] == "handed_out"
    asset.refresh_from_db()
    assert asset.assigned_to == employee()

    returned = it_client.post(f"{url}/return", {}, content_type=JSON)
    assert returned.json()["status"] == "completed"
    asset.refresh_from_db()
    assert asset.status == AssetStatus.IN_STOCK


def test_requester_defaults_to_current_user(it_client):
    (asset,) = in_stock()
    response = post(it_client, assets=[str(asset.pk)], requester=None)
    assert response.json()["requester"]["username"] == "it"


def test_device_in_use_is_refused_and_nothing_is_kept(it_client):
    (asset,) = in_stock()
    asset.status = AssetStatus.IN_USE
    asset.save()
    count = AssetRequest.objects.count()
    response = post(it_client, assets=[str(asset.pk)])
    assert response.status_code == 409
    assert AssetRequest.objects.count() == count


def test_needs_something_to_hand_out(it_client):
    assert post(it_client).status_code == 409


def test_only_for_it(employee_client):
    (asset,) = in_stock()
    assert post(employee_client, assets=[str(asset.pk)]).status_code == 403


def test_list_filters_by_origin(it_client):
    (asset,) = in_stock()
    post(it_client, assets=[str(asset.pk)])
    listed = it_client.get("/api/requests", {"origin": "direct"}).json()["items"]
    assert [r["origin"] for r in listed] == ["direct"]


def test_deactivated_employee_gets_a_clear_message(it_client):
    (asset,) = in_stock()
    gone = employee()
    gone.is_active = False
    gone.save(update_fields=["is_active"])
    response = post(it_client, assets=[str(asset.pk)])
    assert response.status_code == 409
    assert "active employee" in response.json()["detail"]

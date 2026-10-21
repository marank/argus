from apps.inventory.models import Asset
from apps.masterdata.models import AssetModel

JSON = "application/json"


def asset_payload(detail: dict, **changes) -> dict:
    """The asset form as the frontend sends it, built from the detail response."""
    payload = {
        "model": detail["model"]["id"],
        "inventory_number": detail["inventory_number"],
        "serial_number": detail["serial_number"],
        "status": detail["status"],
        "condition": detail["condition"],
        "is_loanable": detail["is_loanable"],
        "location": detail["location"]["id"] if detail["location"] else None,
        "assigned_to": detail["assigned_to"]["id"] if detail["assigned_to"] else None,
        "consumables": [c["id"] for c in detail["consumables"]],
    }
    return {**payload, **changes}


def test_consumables_list_under_new_url(it_client):
    response = it_client.get("/api/inventory/consumables")
    assert response.status_code == 200, response.content
    assert response.json()["count"] == 3


def test_assign_consumables_to_asset(it_client):
    laptop = Asset.objects.filter(model__name="ThinkPad T14 Gen 5").first()
    battery = AssetModel.objects.get(name="SX5x Battery 4680 mAh")
    detail = it_client.get(f"/api/inventory/assets/{laptop.pk}").json()
    assert detail["consumables"] == []

    response = it_client.put(
        f"/api/inventory/assets/{laptop.pk}",
        asset_payload(detail, consumables=[str(battery.pk)]),
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    assert [c["id"] for c in response.json()["consumables"]] == [str(battery.pk)]

    # Assigning a serialized model as consumable is refused.
    phone = AssetModel.objects.get(name="iPhone 16")
    response = it_client.put(
        f"/api/inventory/assets/{laptop.pk}",
        asset_payload(detail, consumables=[str(phone.pk)]),
        content_type=JSON,
    )
    assert response.status_code == 409
    assert list(laptop.consumables.all()) == [battery]


def test_model_consumables_in_asset_detail(it_client):
    printer = Asset.objects.filter(model__name="DeskJet 2820e").first()
    detail = it_client.get(f"/api/inventory/assets/{printer.pk}").json()
    names = {c["name"] for c in detail["model_consumables"]}
    assert names == {"305 black ink cartridge", "305 tri-colour ink cartridge"}


def test_my_consumables_quick_pick(employee_client):
    laptop = Asset.objects.get(model__name="ThinkPad T14 Gen 5", assigned_to__username="employee")
    battery = AssetModel.objects.get(name="SX5x Battery 4680 mAh")
    laptop.consumables.add(battery)

    response = employee_client.get("/api/portal/my-consumables")
    assert response.status_code == 200, response.content
    by_model = {entry["asset"]["model"]["name"]: entry for entry in response.json()}

    printer = {c["name"] for c in by_model["DeskJet 2820e"]["consumables"]}
    assert printer == {"305 black ink cartridge", "305 tri-colour ink cartridge"}
    assert [c["name"] for c in by_model["ThinkPad T14 Gen 5"]["consumables"]] == ["SX5x Battery 4680 mAh"]
    # Devices without matching consumables are left out.
    assert "iPhone 16" not in by_model


def test_quick_pick_skips_consumables_that_cannot_be_requested(employee_client):
    AssetModel.objects.filter(name="305 black ink cartridge").update(is_requestable=False)
    entries = employee_client.get("/api/portal/my-consumables").json()
    names = {c["name"] for entry in entries for c in entry["consumables"]}
    assert names == {"305 tri-colour ink cartridge"}


def test_manual_booking_leaves_reserved_units_alone(it_client):
    from django.utils import timezone

    from apps.accounts.models import User
    from apps.inventory.models import Consumable

    consumable = next(c for c in Consumable.objects.all() if c.available_quantity >= 3)
    response = it_client.post(
        "/api/reservations/direct",
        {
            "title": "New colleague",
            "duration": "permanent",
            "start_date": str(timezone.localdate()),
            "requester": str(User.objects.get(username="employee").pk),
            "consumables": [{"consumable": str(consumable.pk), "quantity": 2}],
        },
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    consumable.refresh_from_db()
    available = consumable.available_quantity
    url = f"/api/inventory/consumables/{consumable.pk}/move"

    response = it_client.post(url, {"delta": -(available + 1), "reason": "issue"}, content_type=JSON)
    assert response.status_code == 409
    assert "2 are reserved" in response.json()["detail"]
    consumable.refresh_from_db()
    assert consumable.quantity == available + 2

    response = it_client.post(url, {"delta": -available, "reason": "issue"}, content_type=JSON)
    assert response.status_code == 200, response.content
    consumable.refresh_from_db()
    assert (consumable.quantity, consumable.reserved_quantity) == (2, 2)

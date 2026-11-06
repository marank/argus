import pytest

from apps.inventory.models import Asset
from apps.inventory.services.mac_address import normalize_mac_address

JSON = "application/json"


@pytest.mark.parametrize(
    "typed",
    ["aa:bb:cc:dd:ee:0f", "AA-BB-CC-DD-EE-0F", "aabbccddee0f", "aabb.ccdd.ee0f", " AA BB CC DD EE 0F "],
)
def test_every_spelling_becomes_pairs_with_colons(typed):
    assert normalize_mac_address(typed) == "AA:BB:CC:DD:EE:0F"


def test_what_is_no_mac_address_stays_as_typed():
    assert normalize_mac_address("") == ""
    assert normalize_mac_address(" AA-BB-CC ") == "AA-BB-CC"
    assert normalize_mac_address("GG:BB:CC:DD:EE:FF") == "GG:BB:CC:DD:EE:FF"


def payload(asset: Asset, **fields):
    return {"model": str(asset.model_id), "inventory_number": asset.inventory_number, **fields}


def test_the_device_form_stores_the_normal_form(it_client):
    asset = Asset.objects.order_by("inventory_number").first()
    assert asset is not None
    response = it_client.put(
        f"/api/inventory/assets/{asset.pk}",
        payload(asset, mac_address="00-1a-2b-3c-4d-5e"),
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    assert response.json()["mac_address"] == "00:1A:2B:3C:4D:5E"

    # The scanner finds the device however the address is written.
    found = it_client.get("/api/inventory/lookup?code=001a2b3c4d5e").json()
    assert [a["id"] for a in found["assets"]] == [str(asset.pk)]


def test_the_device_form_refuses_what_is_no_mac_address(it_client):
    asset = Asset.objects.order_by("inventory_number").first()
    assert asset is not None
    response = it_client.put(
        f"/api/inventory/assets/{asset.pk}", payload(asset, mac_address="00-1a-2b"), content_type=JSON
    )
    assert response.status_code in (400, 422), response.content
    assert "mac_address" in response.content.decode()

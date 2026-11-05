from typing import Any

from apps.masterdata.models import AssetModel, Category


def catalog(client) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """The portal catalog's categories by code and models by name."""
    categories = client.get("/api/portal/catalog").json()
    models = {m["name"]: m for c in categories for m in c["models"]}
    return {c["code"]: c for c in categories}, models


def names(ids: list[str]) -> list[str]:
    return [AssetModel.objects.get(pk=pk).name for pk in ids]


def test_devices_list_compatible_models_from_accessory_categories(employee_client):
    categories, models = catalog(employee_client)
    assert categories["mde-accessories"]["holds_accessories"]
    assert not categories["mde"]["holds_accessories"]
    assert names(models["SX58"]["accessories"]) == [
        "SX5x 5-Slot Charging Cradle",
        "SX5x Battery 4680 mAh",
        "SX5x Trigger Handle",
    ]
    # The link is mutual, but an accessory does not list the device as its accessory.
    assert models["SX5x Trigger Handle"]["accessories"] == []


def test_without_the_mark_compatible_models_are_no_accessories(employee_client):
    Category.objects.filter(code="mde-accessories").update(is_accessory=False)
    categories, models = catalog(employee_client)
    assert not categories["mde-accessories"]["holds_accessories"]
    assert models["SX58"]["accessories"] == []


def test_the_mark_applies_below(employee_client):
    Category.objects.filter(code="mde-accessories").update(is_accessory=False)
    Category.objects.filter(code="mde").update(is_accessory=True)
    categories, models = catalog(employee_client)
    assert categories["mde-accessories"]["holds_accessories"]
    # SX58 is in an accessory category now itself.
    assert models["SX58"]["accessories"] == []


def test_accessories_leave_out_what_cannot_be_requested(employee_client):
    AssetModel.objects.filter(name="SX5x Battery 4680 mAh").update(is_requestable=False)
    _, models = catalog(employee_client)
    assert names(models["SX58"]["accessories"]) == ["SX5x 5-Slot Charging Cradle", "SX5x Trigger Handle"]


def test_category_api_reports_the_inherited_mark(it_client):
    Category.objects.filter(code="mde").update(is_accessory=True)
    Category.objects.filter(code="mde-accessories").update(is_accessory=False)
    child = Category.objects.get(code="mde-accessories")
    data = it_client.get(f"/api/masterdata/categories/{child.pk}").json()
    assert data["is_accessory"] is False
    assert data["holds_accessories"] is True

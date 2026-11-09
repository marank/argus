import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.core.exceptions import BusinessError
from apps.core.models import NumberSequence
from apps.inventory.models import Asset, AssetEvent, AssetEventKind, AssetStatus
from apps.inventory.services import assets as asset_service
from apps.masterdata.models import AssetModel, DeviceNaming, Location

JSON = "application/json"


@pytest.fixture
def it_user(demo) -> User:
    return User.objects.get(username="it")


@pytest.fixture
def sx58(demo) -> AssetModel:
    return AssetModel.objects.select_related("category").get(name="SX58")


def _name_from_sequence(model: AssetModel) -> NumberSequence:
    sequence = NumberSequence.objects.create(name="MDE names", prefix="H", pattern="{prefix}{seq}", padding=3)
    model.category.device_naming = DeviceNaming.SEQUENCE
    model.category.name_sequence = sequence
    model.category.save()
    return sequence


def test_new_device_gets_the_next_free_name_of_its_category(sx58, it_user):
    _name_from_sequence(sx58)
    asset_service.create_asset({"model": sx58.pk, "name": "H002"}, it_user)

    first = asset_service.create_asset({"model": sx58.pk}, it_user)
    # H002 is taken (in any letter case), so the next one skips it.
    asset_service.create_asset({"model": sx58.pk, "name": "h003"}, it_user)
    Asset.objects.filter(name="h003").update(name="H003")
    second = asset_service.create_asset({"model": sx58.pk}, it_user)
    third = asset_service.create_asset({"model": sx58.pk}, it_user)
    assert (first.name, second.name, third.name) == ("H001", "H004", "H005")


def test_name_can_follow_the_inventory_number(sx58, it_user):
    sx58.category.device_naming = DeviceNaming.INVENTORY_NUMBER
    sx58.category.save()
    asset = asset_service.create_asset({"model": sx58.pk}, it_user)
    assert asset.name == asset.inventory_number

    # A name entered by hand wins.
    named = asset_service.create_asset({"model": sx58.pk, "name": "spare-1"}, it_user)
    assert named.name == "spare-1"


def test_category_without_naming_leaves_the_name_empty(sx58, it_user):
    assert asset_service.create_asset({"model": sx58.pk}, it_user).name == ""


def test_category_needs_a_sequence_to_name_from(sx58):
    category = sx58.category
    category.device_naming = DeviceNaming.SEQUENCE
    with pytest.raises(ValidationError) as error:
        category.full_clean()
    assert "name_sequence" in error.value.message_dict

    # The sequence is dropped once names no longer come from it.
    _name_from_sequence(sx58)
    category.device_naming = DeviceNaming.NONE
    category.full_clean()
    assert category.name_sequence is None


def test_only_one_device_in_use_has_a_name(sx58, it_user):
    asset_service.create_asset({"model": sx58.pk, "name": "pc-103"}, it_user)
    other = asset_service.create_asset({"model": sx58.pk}, it_user)
    with pytest.raises(ValidationError) as error:
        asset_service.update_asset(other, {"name": "pc-103"}, it_user)
    assert "name" in error.value.message_dict

    # A retired device keeps its name for the record and does not block it.
    retired = Asset.objects.get(name="pc-103")
    asset_service.update_asset(retired, {"status": AssetStatus.RETIRED}, it_user)
    asset_service.update_asset(other, {"name": "pc-103"}, it_user)
    assert asset_service.name_taken("PC-103")
    assert not asset_service.name_taken("pc-103", exclude=other.pk)


def test_replacement_takes_over_name_holder_and_location(it_client, sx58, it_user):
    employee = User.objects.get(username="employee")
    office = Location.objects.exclude(code="WH").order_by("name")[0]
    old = asset_service.create_asset(
        {"model": sx58.pk, "name": "H017", "assigned_to": employee.pk, "location": office.pk}, it_user
    )
    new = asset_service.create_asset({"model": sx58.pk}, it_user)

    response = it_client.post(
        f"/api/inventory/assets/{old.pk}/replace",
        {"replacement": str(new.pk), "status": "in_repair"},
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert (body["id"], body["name"], body["assigned_to"]["id"]) == (str(new.pk), "H017", str(employee.pk))
    assert body["status"] == "in_use"
    assert body["location"]["id"] == str(office.pk)

    old.refresh_from_db()
    assert (old.name, old.assigned_to, old.status) == ("", None, AssetStatus.IN_REPAIR)
    events = AssetEvent.objects.filter(kind=AssetEventKind.REPLACED)
    assert {(e.asset_id, e.related_asset_id) for e in events} == {(old.pk, new.pk), (new.pk, old.pk)}

    events_out = it_client.get(f"/api/inventory/assets/{old.pk}/events").json()
    replaced = next(e for e in events_out if e["kind"] == "replaced")
    assert replaced["related_asset"]["name"] == "H017"


def test_replacement_must_be_another_device_in_stock(sx58, it_user):
    old = asset_service.create_asset({"model": sx58.pk, "name": "H020"}, it_user)
    in_repair = asset_service.create_asset({"model": sx58.pk, "status": AssetStatus.IN_REPAIR}, it_user)
    spare = asset_service.create_asset({"model": sx58.pk}, it_user)

    with pytest.raises(BusinessError):
        asset_service.replace_asset(old, old, AssetStatus.IN_STOCK, it_user)
    with pytest.raises(BusinessError):
        asset_service.replace_asset(old, in_repair, AssetStatus.IN_STOCK, it_user)
    with pytest.raises(BusinessError):
        asset_service.replace_asset(old, spare, AssetStatus.IN_USE, it_user)

    asset_service.replace_asset(old, spare, AssetStatus.RETIRED, it_user)
    spare.refresh_from_db()
    assert (spare.name, spare.status) == ("H020", AssetStatus.IN_STOCK)


def test_own_category_leaves_out_subcategories(it_client):
    handle = AssetModel.objects.select_related("category__parent").get(name="SX5x Trigger Handle")
    mde = handle.category.parent
    assert mde is not None
    numbers = {
        a["inventory_number"]
        for a in it_client.get(f"/api/inventory/assets?own_category={mde.pk}&page_size=200").json()["items"]
    }
    assert numbers and all(n.startswith("MDE-") for n in numbers)


def test_category_api_carries_the_naming(it_client, sx58):
    sequence = _name_from_sequence(sx58)
    body = it_client.get(f"/api/masterdata/categories/{sx58.category.pk}").json()
    assert (body["device_naming"], body["name_sequence"]["id"]) == ("sequence", str(sequence.pk))

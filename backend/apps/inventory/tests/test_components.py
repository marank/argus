from datetime import date

from apps.inventory.models import Asset, AssetComponent
from apps.masterdata.models import Category, ComponentType

JSON = "application/json"


def sx58() -> Asset:
    asset = Asset.objects.filter(model__name="SX58").order_by("inventory_number").first()
    assert asset is not None
    return asset


def battery() -> ComponentType:
    return ComponentType.objects.get(name="Battery")


def asset_payload(asset: Asset, **fields):
    return {"model": str(asset.model_id), "inventory_number": asset.inventory_number, **fields}


def test_parts_apply_to_their_categories_and_below(it_client):
    mde = Category.objects.get(code="mde")
    accessories = Category.objects.get(code="mde-accessories")
    printers = Category.objects.get(code="printers")
    assert list(ComponentType.for_category(mde)) == [battery()]
    assert list(ComponentType.for_category(accessories)) == [battery()]
    assert not ComponentType.for_category(printers).exists()
    names = [
        t["name"]
        for t in it_client.get(f"/api/masterdata/component-types?category={accessories.pk}").json()["items"]
    ]
    assert names == ["Battery"]


def test_the_device_form_records_the_fitted_parts(it_client):
    asset = sx58()
    response = it_client.put(
        f"/api/inventory/assets/{asset.pk}",
        asset_payload(
            asset,
            identifier="HT60-STD-0002",
            installed_components=[
                {
                    "component_type": str(battery().pk),
                    "serial_number": " BAT-1 ",
                    "installed_on": "2026-01-15",
                }
            ],
        ),
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["identifier"] == "HT60-STD-0002"
    assert data["category"]["identifier_label"] == "CN"
    assert data["installed_components"] == [
        {
            "component_type": {"id": str(battery().pk), "name": "Battery"},
            "serial_number": "BAT-1",
            "installed_on": "2026-01-15",
        }
    ]
    # Leaving the parts out keeps them; an empty entry removes the part.
    it_client.put(f"/api/inventory/assets/{asset.pk}", asset_payload(asset), content_type=JSON)
    assert asset.installed_components.count() == 1
    it_client.put(
        f"/api/inventory/assets/{asset.pk}",
        asset_payload(asset, installed_components=[{"component_type": str(battery().pk)}]),
        content_type=JSON,
    )
    assert asset.installed_components.count() == 0


def test_parts_must_fit_the_category(it_client):
    printer = Asset.objects.filter(model__category__code="printers").first()
    assert printer is not None
    response = it_client.put(
        f"/api/inventory/assets/{printer.pk}",
        asset_payload(
            printer, installed_components=[{"component_type": str(battery().pk), "serial_number": "X"}]
        ),
        content_type=JSON,
    )
    assert response.status_code == 409
    twice = it_client.put(
        f"/api/inventory/assets/{sx58().pk}",
        asset_payload(
            sx58(),
            installed_components=[
                {"component_type": str(battery().pk), "serial_number": "A"},
                {"component_type": str(battery().pk), "serial_number": "B"},
            ],
        ),
        content_type=JSON,
    )
    assert twice.status_code == 409


def test_a_replacement_fits_the_new_part_and_keeps_the_old_serial(it_client):
    asset = sx58()
    AssetComponent.objects.update_or_create(
        asset=asset,
        component_type=battery(),
        defaults={"serial_number": "OLD-1", "installed_on": date(2024, 1, 1)},
    )
    response = it_client.post(
        f"/api/inventory/assets/{asset.pk}/events",
        {
            "kind": "component_replaced",
            "component_type": str(battery().pk),
            "component_serial": "NEW-2",
            "occurred_at": "2026-11-03T10:00:00+01:00",
        },
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    event = response.json()
    assert event["component_type"]["name"] == "Battery"
    assert event["previous_serial"] == "OLD-1"
    part = asset.installed_components.get()
    assert (part.serial_number, part.installed_on) == ("NEW-2", date(2026, 11, 3))


def test_other_kinds_leave_the_parts_alone(it_client):
    asset = sx58()
    before = list(asset.installed_components.values_list("serial_number", flat=True))
    response = it_client.post(
        f"/api/inventory/assets/{asset.pk}/events",
        {"kind": "repair", "component_type": str(battery().pk), "component_serial": "X"},
        content_type=JSON,
    )
    assert response.status_code == 201
    assert response.json()["component_type"] is None
    assert list(asset.installed_components.values_list("serial_number", flat=True)) == before


def test_a_scan_finds_devices_by_identifier_and_part(it_client):
    asset = sx58()
    asset.identifier = "HT60-XYZ"
    asset.save()
    AssetComponent.objects.update_or_create(
        asset=asset, component_type=battery(), defaults={"serial_number": "SCAN-ME"}
    )
    for code in ("ht60-xyz", "SCAN-ME"):
        result = it_client.get(f"/api/inventory/lookup?code={code}").json()
        assert [a["id"] for a in result["assets"]] == [str(asset.pk)], code
    found = it_client.get("/api/inventory/assets?q=SCAN-ME").json()["items"]
    assert [a["id"] for a in found] == [str(asset.pk)]

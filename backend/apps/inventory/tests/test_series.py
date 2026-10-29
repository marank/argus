from apps.inventory.models import Asset, AssetEvent
from apps.masterdata.models import AssetModel, Category, Location

JSON = "application/json"


def test_series_numbers_devices_in_a_row(it_client):
    sx58 = AssetModel.objects.get(name="SX58")
    warehouse = Location.objects.get(code="WH")
    before = Asset.objects.filter(model__category=sx58.category).count()
    preview = it_client.get(f"/api/inventory/assets/series/preview?model={sx58.pk}&count=120").json()
    first, last = f"MDE-{before + 1:04d}", f"MDE-{before + 120:04d}"
    assert (preview["first"], preview["last"]) == (first, last)

    response = it_client.post(
        "/api/inventory/assets/series",
        {"model": str(sx58.pk), "count": 120, "location": str(warehouse.pk), "purchase_price": "1450.00"},
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    numbers = sorted(item["inventory_number"] for item in response.json())
    assert (numbers[0], numbers[-1]) == (first, last)
    created = Asset.objects.filter(inventory_number__in=numbers)
    assert created.count() == 120
    assert set(created.values_list("location", "serial_number", "status")) == {(warehouse.pk, "", "in_stock")}
    assert AssetEvent.objects.filter(asset__in=created, kind=AssetEvent.Kind.CREATED).count() == 120

    # The next series continues where this one ended.
    preview = it_client.get(f"/api/inventory/assets/series/preview?model={sx58.pk}&count=5").json()
    assert preview["first"] == f"MDE-{before + 121:04d}"


def test_subcategory_does_not_inherit_the_sequence(it_client):
    handle = AssetModel.objects.get(name="SX5x Trigger Handle")
    response = it_client.get(f"/api/inventory/assets/series/preview?model={handle.pk}&count=2")
    assert response.json()["first"].startswith("MDA-")

    # Without a sequence of its own, the subcategory does not fall back to the parent's.
    handle.category.number_sequence = None
    handle.category.save()
    response = it_client.get(f"/api/inventory/assets/series/preview?model={handle.pk}&count=2")
    assert response.status_code == 409
    assert Asset.objects.create(model=handle).inventory_number.startswith("INV-")

    numbered = it_client.get("/api/masterdata/models?numbered=true&page_size=100").json()["items"]
    names = {m["name"] for m in numbered}
    assert "SX58" in names and "SX5x Trigger Handle" not in names
    assert all(m["category"]["code"] != "consumables" for m in numbered)


def test_model_sequence_comes_before_the_category_sequence(it_client):
    from apps.core.models import NumberSequence

    handle = AssetModel.objects.get(name="SX5x Trigger Handle")
    unnumbered = AssetModel.objects.filter(category__code="consumables").first()
    assert unnumbered is not None
    quad = NumberSequence.objects.create(name="Quad chargers", prefix="Q", pattern="{prefix}{seq}", padding=3)
    AssetModel.objects.filter(pk__in=[handle.pk, unnumbered.pk]).update(number_sequence=quad)
    handle.refresh_from_db()
    detail = it_client.get(f"/api/masterdata/models/{handle.pk}").json()
    assert detail["number_sequence"]["id"] == detail["effective_number_sequence"]["id"] == str(quad.pk)

    response = it_client.get(f"/api/inventory/assets/series/preview?model={handle.pk}&count=2")
    assert response.json()["first"] == "Q001"
    assert Asset.objects.create(model=handle).inventory_number == "Q001"

    # A model with a sequence of its own counts as numbered, whatever its category.
    numbered = it_client.get("/api/masterdata/models?numbered=true&page_size=100").json()["items"]
    assert unnumbered.name in {m["name"] for m in numbered}


def test_models_show_the_sequence_that_applies(it_client):
    items = it_client.get("/api/masterdata/models?page_size=100").json()["items"]
    sx58 = next(m for m in items if m["name"] == "SX58")
    assert sx58["number_sequence"] is None
    assert sx58["effective_number_sequence"]["name"] == "Mobile data terminals"
    # Consumables get no inventory numbers.
    assert all(m["effective_number_sequence"] is None for m in items if m["tracking"] == "bulk")

    Category.objects.filter(code="mde").update(number_sequence=None)
    sx58 = it_client.get(f"/api/masterdata/models/{sx58['id']}").json()
    assert sx58["effective_number_sequence"]["name"] == "Assets"


def test_series_needs_a_number_sequence(it_client):
    unnumbered = AssetModel.objects.filter(category__code="consumables").first()
    assert unnumbered is not None
    response = it_client.post(
        "/api/inventory/assets/series", {"model": str(unnumbered.pk), "count": 3}, content_type=JSON
    )
    assert response.status_code == 409
    assert not Asset.objects.filter(model=unnumbered).exists()


def test_series_count_is_limited(it_client):
    sx58 = AssetModel.objects.get(name="SX58")
    response = it_client.post(
        "/api/inventory/assets/series", {"model": str(sx58.pk), "count": 501}, content_type=JSON
    )
    assert response.status_code == 422

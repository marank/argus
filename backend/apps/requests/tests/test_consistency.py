from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Asset, AssetStatus
from apps.inventory.services.assets import create_asset
from apps.masterdata.models import AssetModel, Category, Manufacturer
from apps.requests.models import AssetRequest, AssetRequestStatus
from apps.requests.tests.flow import JSON, handover_plan, prepare


def allocated_assets(rid):
    return [
        a.asset
        for i in AssetRequest.objects.get(pk=rid).items.all()
        for a in i.allocations.all()
        if a.asset_id
    ]


def test_any_model_never_picks_accessories(employee_client, it_client):
    """Subcategories hold accessories: "any laptop" must not be filled with a dock."""
    laptops = Category.objects.get(code="laptops")
    accessories = Category.objects.create(
        name="Laptop accessories", code="laptop-accessories", parent=laptops
    )
    manufacturer = Manufacturer.objects.first()
    assert manufacturer is not None
    dock = AssetModel.objects.create(
        name="Dock", designation="Dock", manufacturer=manufacturer, category=accessories
    )
    docked = create_asset({"model": dock.pk, "status": AssetStatus.IN_STOCK}, User.objects.get(username="it"))
    rid = prepare(employee_client, it_client, [{"category": str(laptops.pk), "quantity": 1}])
    assert [asset.model.category_id for asset in allocated_assets(rid)] == [laptops.pk]

    item = AssetRequest.objects.get(pk=rid).items.get()
    candidates = it_client.get(f"/api/requests/items/{item.pk}/candidates").json()["assets"]
    assert str(docked.pk) not in {c["id"] for c in candidates}
    assert all(Asset.objects.get(pk=c["id"]).model.category_id == laptops.pk for c in candidates)


def test_deleting_a_device_with_history_is_refused(employee_client, it_client):
    laptops = Category.objects.get(code="laptops")
    rid = prepare(employee_client, it_client, [{"category": str(laptops.pk), "quantity": 1}])
    asset = allocated_assets(rid)[0]
    response = it_client.delete(f"/api/inventory/assets/{asset.pk}")
    assert response.status_code == 409
    assert Asset.objects.filter(pk=asset.pk).exists()


def test_terminal_hides_lines_without_confirmed_devices(employee_client, it_client, terminal_client):
    laptops = Category.objects.get(code="laptops")
    model = laptops.asset_models.first()
    assert model is not None
    start = timezone.localdate()
    rid = employee_client.post(
        "/api/requests",
        {
            "title": "Test",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
            "items": [
                {"category": str(laptops.pk), "quantity": 1},
                {"asset_model": str(model.pk), "quantity": 1},
            ],
        },
        content_type=JSON,
    ).json()["id"]
    items = AssetRequest.objects.get(pk=rid).items.order_by("position")
    confirmation = [
        {"id": str(items[0].pk), "quantity_confirmed": 1},
        {"id": str(items[1].pk), "quantity_confirmed": 0},
    ]
    it_client.post(f"/api/requests/{rid}/confirm", {"items": confirmation}, content_type=JSON)
    it_client.post(f"/api/requests/{rid}/auto-allocate")
    it_client.post(
        f"/api/requests/{rid}/ready", {"handover_mode": "pickup", **handover_plan()}, content_type=JSON
    )

    pickup = next(p for p in terminal_client.get("/api/terminal/pickups").json() if p["id"] == rid)
    assert "0×" not in pickup["summary"]
    assert pickup["unit_count"] == 1


def test_taking_back_on_the_device_page_returns_it_on_the_request(employee_client, it_client):
    laptops = Category.objects.get(code="laptops")
    rid = prepare(employee_client, it_client, [{"category": str(laptops.pk), "quantity": 1}])
    it_client.post(f"/api/requests/{rid}/hand-out", {"method": "direct"}, content_type=JSON)
    asset = allocated_assets(rid)[0]

    response = it_client.post(f"/api/inventory/assets/{asset.pk}/assign", {"user": None}, content_type=JSON)
    assert response.status_code == 200, response.content
    asset_request = AssetRequest.objects.get(pk=rid)
    assert asset_request.status == AssetRequestStatus.COMPLETED
    asset.refresh_from_db()
    assert asset.status == AssetStatus.IN_STOCK and asset.assigned_to is None


def test_device_set_aside_for_a_request_cannot_be_assigned_elsewhere(employee_client, it_client):
    laptops = Category.objects.get(code="laptops")
    rid = prepare(employee_client, it_client, [{"category": str(laptops.pk), "quantity": 1}])
    asset = allocated_assets(rid)[0]
    it_user = AssetRequest.objects.get(pk=rid).handled_by
    assert it_user is not None

    response = it_client.post(
        f"/api/inventory/assets/{asset.pk}/assign", {"user": str(it_user.pk)}, content_type=JSON
    )
    assert response.status_code == 409
    asset.refresh_from_db()
    assert asset.status == AssetStatus.RESERVED

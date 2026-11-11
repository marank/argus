"""One scan field for a whole request: devices go to the open line they fit."""

from django.db.models import Count

from apps.inventory.models import Asset, AssetStatus
from apps.masterdata.models import AssetModel, Category
from apps.requests.models import AssetRequest

from .flow import JSON, submit


def model_with_spares(count: int = 2) -> AssetModel:
    """A laptop model with at least ``count`` devices in stock."""
    model_id = (
        Asset.objects.filter(model__category__code="laptops", status=AssetStatus.IN_STOCK)
        .values("model")
        .annotate(n=Count("id"))
        .filter(n__gte=count)
        .order_by("model")[0]["model"]
    )
    return AssetModel.objects.get(pk=model_id)


def spares(model: AssetModel) -> list[Asset]:
    return list(Asset.objects.filter(model=model, status=AssetStatus.IN_STOCK).order_by("inventory_number"))


def confirmed(employee_client, it_client, items) -> str:
    response = submit(employee_client, items)
    assert response.status_code == 201, response.content
    rid: str = response.json()["id"]
    response = it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)
    assert response.status_code == 200, response.content
    return rid


def scan(it_client, rid: str, **payload):
    return it_client.post(f"/api/requests/{rid}/allocations/scan", payload, content_type=JSON)


def lines(employee_client, it_client, model: AssetModel) -> str:
    """A request for any laptop and, below it, for this model by name."""
    laptops = str(Category.objects.get(code="laptops").pk)
    return confirmed(
        employee_client,
        it_client,
        [{"category": laptops, "quantity": 1}, {"asset_model": str(model.pk), "quantity": 1}],
    )


def allocated(body) -> list[list[str]]:
    return [[a["asset"]["inventory_number"] for a in item["allocations"]] for item in body["items"]]


def test_scan_fills_the_line_naming_the_model_first(employee_client, it_client):
    model = model_with_spares()
    first, second = spares(model)[:2]
    rid = lines(employee_client, it_client, model)

    body = scan(it_client, rid, code=first.inventory_number).json()
    assert allocated(body) == [[], [first.inventory_number]]
    # The named line is full, so the next one goes to "any laptop".
    body = scan(it_client, rid, asset=str(second.pk)).json()
    assert allocated(body) == [[second.inventory_number], [first.inventory_number]]
    assert body["items"][0]["category_name"] == "Laptops"
    assert body["items"][1]["category_icon"]

    # Both laptop lines are full now.
    other = Asset.objects.filter(model__category__code="laptops", status=AssetStatus.IN_STOCK)[0]
    assert scan(it_client, rid, code=other.inventory_number).status_code >= 400


def test_scan_by_serial_and_unknown_codes(employee_client, it_client):
    model = model_with_spares()
    laptop = spares(model)[0]
    rid = lines(employee_client, it_client, model)

    response = scan(it_client, rid, code=laptop.serial_number)
    assert response.status_code == 200, response.content
    assert scan(it_client, rid, code="NO-SUCH-CODE").status_code >= 400
    assert scan(it_client, rid).status_code >= 400


def test_scan_refuses_devices_no_open_line_takes(employee_client, it_client):
    model = model_with_spares()
    rid = lines(employee_client, it_client, model)
    dock = Asset.objects.exclude(model__category__code="laptops").filter(status=AssetStatus.IN_STOCK)[0]
    response = scan(it_client, rid, code=dock.inventory_number)
    assert response.status_code >= 400
    assert dock.inventory_number in response.json()["detail"]


def test_search_offers_pool_devices_for_the_open_lines(employee_client, it_client):
    model = model_with_spares()
    laptop = spares(model)[0]
    rid = lines(employee_client, it_client, model)

    body = it_client.get(f"/api/requests/{rid}/candidates", {"q": laptop.inventory_number}).json()
    named_line = str(AssetRequest.objects.get(pk=rid).items.get(asset_model=model).pk)
    # Offered once, for the line naming its model.
    assert [(m["item"], m["asset"]["id"]) for m in body["matches"]] == [(named_line, str(laptop.pk))]
    pool = {p["item"]: p["available"] for p in body["pool"]}
    assert pool[named_line] == len(spares(model))

    # Without a search only the pool counts.
    assert it_client.get(f"/api/requests/{rid}/candidates").json()["matches"] == []


def test_scan_records_devices_after_a_hand_out_without_them(employee_client, it_client):
    model = model_with_spares()
    laptop = spares(model)[0]
    rid = lines(employee_client, it_client, model)
    it_client.post(f"/api/requests/{rid}/hand-out-unrecorded", {}, content_type=JSON)

    response = scan(it_client, rid, code=laptop.inventory_number)
    assert response.status_code == 200, response.content
    laptop.refresh_from_db()
    assert laptop.status == AssetStatus.IN_USE

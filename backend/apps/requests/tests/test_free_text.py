from datetime import date, timedelta

from apps.inventory.models import Asset
from apps.masterdata.models import Category, Manufacturer

JSON = "application/json"


def submit(client, items):
    start = date.today() + timedelta(days=2)
    response = client.post(
        "/api/requests",
        {
            "title": "Special request",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=3)).isoformat(),
            "items": items,
        },
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    return response.json()


def test_free_text_lines_need_resolution(employee_client, it_client):
    laptops = Category.objects.get(code="laptops")
    asset_request = submit(
        employee_client,
        [
            {"category": str(laptops.pk), "description": "Laptop with 64 GB RAM", "quantity": 1},
            {"description": "Label printer", "quantity": 1},
        ],
    )
    in_group, general = asset_request["items"]
    assert in_group["is_free_text"] and in_group["label"] == "Laptops: Laptop with 64 GB RAM"
    assert general["label"] == "Label printer"

    rid = asset_request["id"]
    it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)

    # Free text is never filled automatically, so nothing random lands in the request.
    assert it_client.post(f"/api/requests/{rid}/auto-allocate").json()["allocated"] == 0
    assert it_client.get(f"/api/requests/items/{in_group['id']}/candidates").json()["assets"] == []
    assert it_client.post(f"/api/requests/{rid}/ready", {}, content_type=JSON).status_code == 409

    needs = it_client.get("/api/procurement/needs").json()["requests"]
    need = next(n for n in needs if n["asset_request_item"]["id"] == general["id"])
    assert need["available"] == 0 and need["to_order"] == 1

    # IT creates a model for the laptop line and maps it.
    model = it_client.post(
        "/api/masterdata/models",
        {
            "name": "ThinkPad P16s 64GB",
            "designation": "21K9",
            "manufacturer": str(Manufacturer.objects.get(name="Lenovo").pk),
            "category": str(laptops.pk),
        },
        content_type=JSON,
    ).json()
    response = it_client.post(
        f"/api/requests/{rid}/items/{in_group['id']}/resolve",
        {"asset_model": model["id"]},
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    resolved = response.json()["items"][0]
    assert not resolved["is_free_text"]
    assert resolved["asset_model"]["id"] == model["id"]
    assert resolved["description"] == "Laptop with 64 GB RAM"  # kept for context
    assert not Asset.objects.filter(model_id=model["id"]).exists()


def test_empty_line_is_rejected(employee_client):
    start = date.today() + timedelta(days=1)
    response = employee_client.post(
        "/api/requests",
        {
            "title": "x",
            "duration": "permanent",
            "start_date": start.isoformat(),
            "items": [{"description": "   ", "quantity": 1}],
        },
        content_type=JSON,
    )
    assert response.status_code == 422


def test_any_model_can_be_disabled_per_group(employee_client):
    accessories = Category.objects.get(code="mde-accessories")
    start = date.today() + timedelta(days=1)
    item = {"category": str(accessories.pk), "quantity": 2}
    payload = {
        "title": "Handles",
        "duration": "permanent",
        "start_date": start.isoformat(),
        "items": [item],
    }
    response = employee_client.post("/api/requests", payload, content_type=JSON)
    assert response.status_code == 409
    # A custom request within the group is still possible.
    item["description"] = "Handle with strap"
    assert employee_client.post("/api/requests", payload, content_type=JSON).status_code == 201

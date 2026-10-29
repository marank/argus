"""Booking deliveries: open quantities and lines that are not on the order."""

import uuid

from apps.masterdata.models import AssetModel, Location

JSON = "application/json"


def ordered(client, quantity=2) -> dict:
    model = AssetModel.objects.filter(tracking=AssetModel.Tracking.BULK).first()
    assert model is not None
    order = client.post(
        "/api/procurement/orders",
        {"lines": [{"asset_model": str(model.pk), "quantity": quantity}]},
        content_type=JSON,
    ).json()
    response = client.post(f"/api/procurement/orders/{order['id']}/ordered", {}, content_type=JSON)
    assert response.status_code == 200, response.content
    return order


def receive(client, order, line, quantity):
    location = Location.objects.first()
    assert location is not None
    return client.post(
        f"/api/procurement/orders/{order['id']}/receive",
        {"receipts": [{"line": line, "quantity": quantity, "location": str(location.pk)}]},
        content_type=JSON,
    )


def test_receive_in_parts_up_to_the_open_quantity(it_client):
    order = ordered(it_client, quantity=3)
    line = order["lines"][0]["id"]
    response = receive(it_client, order, line, 2)
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "partially_received"
    response = receive(it_client, order, line, 2)
    assert response.status_code == 409
    assert "Only 1 units" in response.json()["detail"]
    response = receive(it_client, order, line, 1)
    assert response.json()["status"] == "received"


def test_line_of_another_order_is_not_found(it_client):
    order, other = ordered(it_client), ordered(it_client)
    for line in (other["lines"][0]["id"], str(uuid.uuid4())):
        response = receive(it_client, order, line, 1)
        assert response.status_code == 404, response.content


def test_changing_lines_of_a_placed_order_changes_nothing(it_client):
    order = ordered(it_client)
    model = AssetModel.objects.filter(tracking=AssetModel.Tracking.BULK).first()
    assert model is not None
    response = it_client.put(
        f"/api/procurement/orders/{order['id']}",
        {"notes": "changed", "lines": [{"asset_model": str(model.pk), "quantity": 9}]},
        content_type=JSON,
    )
    assert response.status_code == 409
    assert it_client.get(f"/api/procurement/orders/{order['id']}").json()["notes"] == ""

from apps.activity.models import Activity
from apps.masterdata.models import AssetModel, Location
from apps.procurement.models import PurchaseOrder

JSON = "application/json"


def order(client, model: AssetModel, quantity: int) -> str:
    response = client.post(
        "/api/procurement/orders",
        {"lines": [{"asset_model": str(model.pk), "quantity": quantity}]},
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    pk: str = response.json()["id"]
    return pk


def test_order_steps_and_one_row_per_delivery(it_client, fresh):
    model = AssetModel.objects.get(name="SX58")
    pk = order(it_client, model, 3)
    it_client.post(f"/api/procurement/orders/{pk}/ordered", {"supplier_reference": "AB-1"}, content_type=JSON)
    line = PurchaseOrder.objects.get(pk=pk).lines.get()
    response = it_client.post(
        f"/api/procurement/orders/{pk}/receive",
        {
            "receipts": [
                {"line": str(line.pk), "quantity": 3, "location": str(Location.objects.get(code="WH").pk)}
            ]
        },
        content_type=JSON,
    )
    assert response.status_code == 200, response.content

    kinds = list(Activity.objects.order_by("occurred_at", "id").values_list("kind", "quantity", "detail"))
    assert kinds == [("order_created", 1, ""), ("order_placed", None, "AB-1"), ("order_received", 3, "")]
    assert set(Activity.objects.values_list("area", flat=True)) == {"procurement"}


def test_cancel_and_delete_are_recorded(it_client, fresh):
    model = AssetModel.objects.get(name="SX58")
    cancelled, deleted = order(it_client, model, 1), order(it_client, model, 1)
    it_client.post(f"/api/procurement/orders/{cancelled}/cancel")
    number = PurchaseOrder.objects.get(pk=deleted).number
    assert it_client.delete(f"/api/procurement/orders/{deleted}").status_code == 204

    assert Activity.objects.filter(kind="order_cancelled", subject_id=cancelled).exists()
    gone = Activity.objects.get(kind="order_deleted")
    assert gone.subject_id is None and gone.subject_label.startswith(number)

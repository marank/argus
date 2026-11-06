from apps.masterdata.models import AssetModel

JSON = "application/json"


def put(client, model: AssetModel, **fields):
    data = {
        "name": model.name,
        "designation": model.designation,
        "manufacturer": str(model.manufacturer_id),
        "category": str(model.category_id),
        "tracking": model.tracking,
        **fields,
    }
    return client.put(f"/api/masterdata/models/{model.pk}", data, content_type=JSON)


def test_a_model_names_its_predecessor(it_client):
    sx58 = AssetModel.objects.get(name="SX58")
    successor = it_client.post(
        "/api/masterdata/models",
        {
            "name": "SX58e",
            "designation": "SX58E",
            "manufacturer": str(sx58.manufacturer_id),
            "category": str(sx58.category_id),
            "predecessor": str(sx58.pk),
        },
        content_type=JSON,
    )
    assert successor.status_code == 201, successor.content
    assert successor.json()["predecessor"]["full_name"] == sx58.full_name
    assert list(sx58.successors.values_list("name", flat=True)) == ["SX58e"]


def test_a_model_cannot_succeed_itself_or_its_successors(it_client):
    first = AssetModel.objects.get(name="SX58")
    second = AssetModel.objects.get(name="SX5x Trigger Handle")
    third = AssetModel.objects.get(name="SX5x Battery 4680 mAh")
    assert put(it_client, first, predecessor=str(first.pk)).status_code == 422
    assert put(it_client, second, predecessor=str(first.pk)).status_code == 200
    assert put(it_client, third, predecessor=str(second.pk)).status_code == 200
    response = put(it_client, first, predecessor=str(third.pk))
    assert response.status_code == 422
    assert "successors" in response.content.decode()

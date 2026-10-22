from apps.masterdata.models import AssetModel, Category, Manufacturer


def payload(**fields):
    return {
        "name": "4-slot charging cradle",
        "designation": "CRD-SX5X-4SC",
        "manufacturer": str(Manufacturer.objects.get(name="Scanova").pk),
        "category": str(Category.objects.get(code="mde-accessories").pk),
        **fields,
    }


def test_models_may_share_a_name_but_not_a_designation(it_client):
    first = it_client.post("/api/masterdata/models", payload(), content_type="application/json")
    assert first.status_code == 201, first.json()
    assert first.json()["designation"] == "CRD-SX5X-4SC"

    same_name = it_client.post(
        "/api/masterdata/models", payload(designation="CRD-TC2X-4SC"), content_type="application/json"
    )
    assert same_name.status_code == 201, same_name.json()
    assert AssetModel.objects.filter(name="4-slot charging cradle").count() == 2

    same_designation = it_client.post(
        "/api/masterdata/models", payload(name="Cradle"), content_type="application/json"
    )
    assert same_designation.status_code == 422
    assert AssetModel.objects.filter(designation="CRD-SX5X-4SC").count() == 1


def test_models_are_found_by_designation(it_client):
    it_client.post("/api/masterdata/models", payload(), content_type="application/json")
    items = it_client.get("/api/masterdata/models?q=SX5X-4SC").json()["items"]
    assert [m["name"] for m in items] == ["4-slot charging cradle"]

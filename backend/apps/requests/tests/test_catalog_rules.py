from datetime import timedelta
from typing import Any

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.core.models import SiteSettings
from apps.masterdata.models import AssetModel, Category, CategoryKind, ModelChoice

JSON = "application/json"


def request(client, item: dict[str, Any]):
    start = timezone.localdate() + timedelta(days=2)
    data = {
        "title": "Catalog check",
        "duration": "temporary",
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=3)).isoformat(),
        "items": [{"quantity": 1, **item}],
    }
    return client.post("/api/requests", data, content_type=JSON)


def hardware_model() -> AssetModel:
    model = AssetModel.objects.filter(category__kind=CategoryKind.HARDWARE).first()
    assert model is not None
    return model


@pytest.mark.parametrize("field", ["is_requestable", "is_active"])
def test_employees_cannot_request_models_off_the_catalog(employee_client, field):
    model = hardware_model()
    setattr(model, field, False)
    model.save()
    response = request(employee_client, {"asset_model": str(model.pk)})
    assert response.status_code == 409, response.content
    assert "cannot be requested" in response.json()["detail"]


def test_employees_cannot_request_from_hidden_categories(employee_client):
    model = hardware_model()
    Category.objects.filter(pk=model.category_id).update(is_requestable=False)
    assert request(employee_client, {"asset_model": str(model.pk)}).status_code == 409
    assert request(employee_client, {"category": str(model.category_id)}).status_code == 409
    response = request(employee_client, {"category": str(model.category_id), "description": "Something"})
    assert response.status_code == 409


def test_software_needs_the_software_feature(employee_client):
    software = AssetModel.objects.filter(
        category__kind=CategoryKind.SOFTWARE, is_requestable=True, is_active=True
    ).first()
    assert software is not None
    assert request(employee_client, {"asset_model": str(software.pk)}).status_code == 201
    SiteSettings.objects.update(flags={"software_requests": False})
    assert request(employee_client, {"asset_model": str(software.pk)}).status_code == 409


def test_it_may_record_anything(it_client):
    model = hardware_model()
    model.is_requestable = False
    model.save()
    assert request(it_client, {"asset_model": str(model.pk)}).status_code == 201


def test_unknown_or_inactive_requester_is_refused_with_a_message(it_client):
    sales = User.objects.get(username="sales")
    sales.is_active = False
    sales.save()
    model = hardware_model()
    for requester in (str(sales.pk), "00000000-0000-0000-0000-000000000000"):
        start = timezone.localdate() + timedelta(days=2)
        data = {
            "title": "On behalf",
            "duration": "permanent",
            "start_date": start.isoformat(),
            "requester": requester,
            "items": [{"quantity": 1, "asset_model": str(model.pk)}],
        }
        response = it_client.post("/api/requests", data, content_type=JSON)
        assert response.status_code == 409, response.content
        assert "active employee" in response.json()["detail"]


def test_where_it_picks_the_model_employees_request_any(employee_client, it_client):
    mde = Category.objects.get(code="mde")
    mde.model_choice = ModelChoice.ANY_ONLY
    mde.save()
    sx58 = AssetModel.objects.get(name="SX58")
    response = request(employee_client, {"asset_model": str(sx58.pk)})
    assert response.status_code == 409
    assert "IT picks the model" in response.json()["detail"]
    assert request(employee_client, {"category": str(mde.pk)}).status_code == 201
    catalog = {c["code"]: c for c in employee_client.get("/api/portal/catalog").json()}
    assert catalog["mde"]["model_choice"] == "any_only"


def test_where_the_type_matters_a_model_is_needed(employee_client):
    mde = Category.objects.get(code="mde")
    mde.model_choice = ModelChoice.SPECIFIC_ONLY
    mde.save()
    response = request(employee_client, {"category": str(mde.pk)})
    assert response.status_code == 409
    assert "choose a specific model" in response.json()["detail"]

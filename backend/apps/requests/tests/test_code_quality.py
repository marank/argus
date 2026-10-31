"""Lookups by scanned code and query counts of the employee's pages."""

from datetime import timedelta
from typing import Any

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Asset
from apps.inventory.services.issues import report_issue

JSON = "application/json"


def confirmed_request(employee_client, it_client, model) -> dict[str, Any]:
    start = timezone.localdate() + timedelta(days=2)
    asset_request = employee_client.post(
        "/api/requests",
        {
            "title": "Scan test",
            "duration": "permanent",
            "start_date": start.isoformat(),
            "items": [{"asset_model": str(model.pk), "quantity": 1}],
        },
        content_type=JSON,
    ).json()
    response = it_client.post(
        f"/api/requests/{asset_request['id']}/confirm", {"items": []}, content_type=JSON
    )
    assert response.status_code == 200, response.content
    body: dict[str, Any] = response.json()
    return body


def test_colliding_serial_numbers_are_not_guessed(employee_client, it_client):
    # Serial numbers are unique per model only: two manufacturers may use the same one.
    first = Asset.objects.filter(assigned_to__isnull=True, status="in_stock").first()
    assert first is not None
    second = Asset.objects.filter(status="in_stock").exclude(model=first.model).first()
    assert second is not None
    second.serial_number = first.serial_number = "SAME-123"
    first.save()
    second.save()
    asset_request = confirmed_request(employee_client, it_client, first.model)
    item = asset_request["items"][0]["id"]

    url = f"/api/requests/{asset_request['id']}/allocations"
    response = it_client.post(url, {"item": item, "code": "same-123"}, content_type=JSON)
    assert response.status_code == 409
    assert "inventory number" in response.json()["detail"]
    response = it_client.post(url, {"item": item, "code": first.inventory_number}, content_type=JSON)
    assert response.status_code == 200, response.content


def test_my_issues_load_their_last_messages_at_once(employee_client):
    employee = User.objects.get(username="employee")
    assets = list(Asset.objects.filter(assigned_to=employee).order_by("pk")[:1]) or list(
        Asset.objects.order_by("pk")[:1]
    )
    for _i in range(3):
        report_issue(assets[0], employee, "defect", "Broken")
    with CaptureQueriesContext(connection) as few:
        employee_client.get("/api/portal/my-issues")
    for _i in range(5):
        report_issue(assets[0], employee, "defect", "Broken")
    with CaptureQueriesContext(connection) as more:
        response = employee_client.get("/api/portal/my-issues")
    assert len(response.json()) == 8
    assert len(more) == len(few)

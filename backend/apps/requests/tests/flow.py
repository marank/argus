"""Steps of the request workflow through the API, shared by the request tests."""

from datetime import date, timedelta

from django.test import Client
from django.utils import timezone

from apps.masterdata.models import Category, Location

JSON = "application/json"


def handover_plan() -> dict[str, str]:
    """Date and place for marking a request ready: the ready message needs both."""
    return {
        "pickup_at": (timezone.now() + timedelta(days=1)).isoformat(),
        "pickup_location": str(Location.objects.get(code="HQ-IT-00").pk),
    }


def laptops() -> list[dict[str, object]]:
    return [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}]


def submit(client: Client, items, duration="temporary", start: date | None = None):
    start = start or timezone.localdate()
    data = {"title": "Test", "duration": duration, "start_date": start.isoformat(), "items": items}
    if duration == "temporary":
        data["end_date"] = (start + timedelta(days=3)).isoformat()
    return client.post("/api/requests", data, content_type=JSON)


def prepare(employee_client, it_client, items, duration="temporary", handover_mode="collect", **ready):
    """Submit, confirm, allocate and mark ready; returns the request id."""
    response = submit(employee_client, items, duration)
    assert response.status_code == 201, response.content
    rid = response.json()["id"]
    it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)
    it_client.post(f"/api/requests/{rid}/auto-allocate")
    response = it_client.post(
        f"/api/requests/{rid}/ready",
        {"handover_mode": handover_mode, **handover_plan(), **ready},
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    return rid


def handed_out(employee_client, it_client, duration="temporary"):
    """A laptop request handed out directly; returns the request id."""
    rid = prepare(employee_client, it_client, laptops(), duration=duration)
    it_client.post(f"/api/requests/{rid}/hand-out", {"method": "direct"}, content_type=JSON)
    return rid

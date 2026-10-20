from datetime import date, timedelta
from importlib import import_module

from django.apps import apps

from apps.accounts.models import User
from apps.masterdata.models import Category
from apps.reservations.models import Reservation, ReservationEvent

JSON = "application/json"


def kinds(body: dict) -> list[str]:
    return [event["kind"] for event in body["events"]]


def run_cycle(employee_client, it_client) -> str:
    """Request, confirm, allocate, ready, hand out, extend, take back."""
    start = date.today()
    created = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=2)).isoformat(),
            "items": [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}],
        },
        content_type=JSON,
    ).json()
    url = f"/api/reservations/{created['id']}"
    it_client.post(f"{url}/confirm", {"comment": "Fine"}, content_type=JSON)
    it_client.post(f"{url}/assign", {"assignee": str(User.objects.get(username="it").pk)}, content_type=JSON)
    it_client.post(f"{url}/auto-allocate")
    it_client.post(f"{url}/ready", {"handover_mode": "collect"}, content_type=JSON)
    it_client.post(f"{url}/hand-out", {}, content_type=JSON)
    new_end = (start + timedelta(days=9)).isoformat()
    it_client.post(f"{url}/extend", {"end_date": new_end}, content_type=JSON)
    it_client.post(f"{url}/return", {}, content_type=JSON)
    return created["id"]


def test_every_step_is_recorded(employee_client, it_client):
    pk = run_cycle(employee_client, it_client)
    body = it_client.get(f"/api/reservations/{pk}").json()
    assert kinds(body) == [
        "created",
        "confirmed",
        "assigned",
        "allocated",
        "ready",
        "handed_out",
        "extended",
        "returned",
        "completed",
    ]
    events = {e["kind"]: e for e in body["events"]}
    assert events["created"]["actor"]["username"] == "employee"
    assert events["confirmed"]["data"] == {"comment": "Fine"}
    assert events["confirmed"]["actor"]["username"] == "it"
    assert events["ready"]["data"]["handover_mode"] == "collect"
    # Plain values that stay readable, e.g. the inventory number and the old return date.
    assert events["allocated"]["data"]["items"] == events["returned"]["data"]["items"]
    assert events["extended"]["data"]["previous"] == (date.today() + timedelta(days=2)).isoformat()


def test_employee_sees_their_part(employee_client, it_client):
    pk = run_cycle(employee_client, it_client)
    body = employee_client.get(f"/api/reservations/{pk}").json()
    assert "assigned" not in kinds(body)
    assert "allocated" not in kinds(body)
    assert "handed_out" in kinds(body)


def test_released_allocation_stays_in_history(employee_client, it_client):
    start = date.today() + timedelta(days=1)
    created = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "permanent",
            "start_date": start.isoformat(),
            "items": [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}],
        },
        content_type=JSON,
    ).json()
    url = f"/api/reservations/{created['id']}"
    it_client.post(f"{url}/confirm", {}, content_type=JSON)
    body = it_client.post(f"{url}/auto-allocate").json()["reservation"]
    allocation = body["items"][0]["allocations"][0]
    body = it_client.delete(f"{url}/allocations/{allocation['id']}").json()
    released = [e for e in body["events"] if e["kind"] == "released"]
    assert released[0]["data"]["items"] == [allocation["asset"]["inventory_number"]]


def test_backfill_restores_history_of_older_requests(employee_client, it_client):
    pk = run_cycle(employee_client, it_client)
    ReservationEvent.objects.all().delete()
    backfill = import_module("apps.reservations.migrations.0016_backfill_reservation_events").backfill
    backfill(apps, None)

    restored = list(Reservation.objects.get(pk=pk).events.values_list("kind", flat=True))
    # Marking ready, the assignment and the extension were not kept before.
    assert restored == ["created", "confirmed", "allocated", "handed_out", "returned", "completed"]
    # Requests that already have a history are left alone.
    backfill(apps, None)
    assert Reservation.objects.get(pk=pk).events.count() == len(restored)

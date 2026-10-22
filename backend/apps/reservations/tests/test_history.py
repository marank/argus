from datetime import date, timedelta
from importlib import import_module

from django.apps import apps
from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Asset
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
    assert events["ready"]["data"]["items"] == events["returned"]["data"]["items"]
    assert events["extended"]["data"]["previous"] == (date.today() + timedelta(days=2)).isoformat()


def test_employee_sees_their_part(employee_client, it_client):
    pk = run_cycle(employee_client, it_client)
    body = employee_client.get(f"/api/reservations/{pk}").json()
    assert "assigned" not in kinds(body)
    assert "allocated" not in kinds(body)
    assert "handed_out" in kinds(body)


def _confirmed_laptops(employee_client, it_client, quantity=1):
    created = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "permanent",
            "start_date": (date.today() + timedelta(days=1)).isoformat(),
            "items": [{"category": str(Category.objects.get(code="laptops").pk), "quantity": quantity}],
        },
        content_type=JSON,
    ).json()
    url = f"/api/reservations/{created['id']}"
    it_client.post(f"{url}/confirm", {}, content_type=JSON)
    item = Reservation.objects.get(pk=created["id"]).items.get()
    laptops = Asset.objects.filter(model__category=item.category, status=Asset.Status.IN_STOCK)
    return url, item, list(laptops.order_by("inventory_number")[:2])


def test_preparing_leaves_no_trace(employee_client, it_client):
    """Scanning, taking out and scanning again is work in progress, not history."""
    url, item, (laptop, _) = _confirmed_laptops(employee_client, it_client)
    device_history = laptop.events.count()

    def scan():
        return it_client.post(
            f"{url}/allocations", {"item": str(item.pk), "asset": str(laptop.pk)}, content_type=JSON
        ).json()

    body = scan()
    it_client.delete(f"{url}/allocations/{body['items'][0]['allocations'][0]['id']}")
    body = scan()
    assert kinds(body) == ["created", "confirmed"]
    assert laptop.events.count() == device_history

    body = it_client.post(f"{url}/ready", {"handover_mode": "collect"}, content_type=JSON).json()
    assert body["events"][-1]["data"]["items"] == [laptop.inventory_number]
    assert laptop.events.count() == device_history


def test_ready_again_lists_what_changed(employee_client, it_client):
    url, item, (first, second) = _confirmed_laptops(employee_client, it_client)
    device_history = first.events.count()
    body = it_client.post(
        f"{url}/allocations", {"item": str(item.pk), "asset": str(first.pk)}, content_type=JSON
    ).json()
    it_client.post(f"{url}/ready", {"handover_mode": "collect"}, content_type=JSON)

    # Swapped while ready: back in preparation, then ready with the other laptop.
    body = it_client.delete(f"{url}/allocations/{body['items'][0]['allocations'][0]['id']}").json()
    assert kinds(body)[-1] == "reopened"
    it_client.post(f"{url}/allocations", {"item": str(item.pk), "asset": str(second.pk)}, content_type=JSON)
    body = it_client.post(f"{url}/ready", {"handover_mode": "collect"}, content_type=JSON).json()

    again = body["events"][-1]
    assert again["kind"] == "ready"
    assert again["data"]["added"] == [second.inventory_number]
    assert again["data"]["removed"] == [first.inventory_number]
    assert "items" not in again["data"]
    first.refresh_from_db()
    assert first.status == Asset.Status.IN_STOCK
    # Set aside and given back without being handed out: nothing for the device's history.
    assert first.events.count() == device_history


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


def test_confirming_leaves_the_handover_to_marking_ready(employee_client, it_client):
    """Confirming only tells the employee it is fine; date and place are set when it is ready."""
    pk = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "permanent",
            "start_date": date.today().isoformat(),
            "items": [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}],
        },
        content_type=JSON,
    ).json()["id"]
    url = f"/api/reservations/{pk}"
    pickup = (timezone.now() + timedelta(days=1)).replace(microsecond=0).isoformat()
    body = it_client.post(f"{url}/confirm", {"pickup_at": pickup}, content_type=JSON).json()
    assert body["pickup_at"] is None

    it_client.post(f"{url}/auto-allocate")
    body = it_client.post(
        f"{url}/ready", {"handover_mode": "collect", "pickup_at": pickup}, content_type=JSON
    ).json()
    assert body["pickup_at"] is not None
    # One step, not "handover changed" and "ready" for the same click.
    assert kinds(body)[-1] == "ready"
    assert "rescheduled" not in kinds(body)
    assert body["events"][-1]["data"]["pickup_at"]

from datetime import date, timedelta

from django.utils import timezone

from apps.reservations.models import Reservation


def fetch(client, **params):
    today = timezone.localdate()
    query = {
        "start": (today - timedelta(days=10)).isoformat(),
        "end": (today + timedelta(days=40)).isoformat(),
    }
    query.update(params)
    response = client.get("/api/calendar", query)
    assert response.status_code == 200, response.content
    return response.json()


def test_calendar_shows_loans_and_pickups(it_client):
    entries = fetch(it_client)
    kinds = {e["kind"] for e in entries}
    assert {"loan", "pickup"} <= kinds

    workshop = Reservation.objects.get(title="Training workshop")
    loan = next(e for e in entries if e["id"] == f"loan-{workshop.pk}")
    # Ends are exclusive so a span from Mon to Wed covers Wed as well.
    assert loan["end"] == (workshop.end_date + timedelta(days=1)).isoformat()
    assert loan["link"] == {"name": "reservation", "id": str(workshop.pk)}


def test_permanent_requests_are_not_shown_as_loans(it_client):
    entries = fetch(it_client)
    permanent = Reservation.objects.filter(duration=Reservation.Duration.PERMANENT)
    loan_ids = {e["id"] for e in entries if e["kind"] == "loan"}
    assert not loan_ids & {f"loan-{r.pk}" for r in permanent}


def test_overdue_returns_appear_today(it_client):
    workshop = Reservation.objects.get(title="Training workshop")
    Reservation.objects.filter(pk=workshop.pk).update(
        status=Reservation.Status.HANDED_OUT,
        start_date=date.today() - timedelta(days=9),
        end_date=date.today() - timedelta(days=2),
    )
    entry = next(e for e in fetch(it_client, kinds=["return"]) if e["id"] == f"return-{workshop.pk}")
    assert entry["overdue"] is True
    assert entry["start"] == timezone.localdate().isoformat()


def test_calendar_is_for_it_only(employee_client):
    assert (
        employee_client.get("/api/calendar", {"start": "2026-01-01", "end": "2026-01-31"}).status_code == 403
    )


def test_warranty_ends_are_grouped_per_day(it_client):
    from apps.inventory.models import Asset

    day = timezone.localdate() + timedelta(days=5)
    ids = list(Asset.objects.values_list("pk", flat=True)[:2])
    Asset.objects.filter(pk__in=ids).update(warranty_until=day)
    entries = [e for e in fetch(it_client, kinds=["warranty"]) if e["start"] == day.isoformat()]
    assert len(entries) == 1
    assert entries[0]["title"] == "2" and len(entries[0]["details"]) == 2

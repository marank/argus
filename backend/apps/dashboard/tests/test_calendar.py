from datetime import date, timedelta

from django.utils import timezone

from apps.requests.models import AssetRequest, AssetRequestStatus


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

    workshop = AssetRequest.objects.get(title="Training workshop")
    loan = next(e for e in entries if e["id"] == f"loan-{workshop.pk}")
    # Ends are exclusive so a span from Mon to Wed covers Wed as well.
    assert workshop.end_date is not None
    assert loan["end"] == (workshop.end_date + timedelta(days=1)).isoformat()
    assert loan["link"] == {"name": "request", "id": str(workshop.pk)}


def test_unconfirmed_requests_are_shown_as_pickups_on_their_day(it_client):
    """Without an appointment the planned day counts, confirmed or not."""
    headset = AssetRequest.objects.get(title="New headset")
    assert headset.status == AssetRequestStatus.SUBMITTED and headset.pickup_at is None
    entry = next(e for e in fetch(it_client, kinds=["pickup"]) if e["id"] == f"pickup-{headset.pk}")
    assert entry["start"] == headset.start_date.isoformat()
    assert entry["all_day"] is True
    assert entry["status"] == "submitted"

    wished = headset.start_date + timedelta(days=3)
    AssetRequest.objects.filter(pk=headset.pk).update(requested_pickup_date=wished)
    entry = next(e for e in fetch(it_client, kinds=["pickup"]) if e["id"] == f"pickup-{headset.pk}")
    assert entry["start"] == wished.isoformat()


def test_permanent_requests_are_not_shown_as_loans(it_client):
    entries = fetch(it_client)
    permanent = AssetRequest.objects.filter(duration=AssetRequest.Duration.PERMANENT)
    loan_ids = {e["id"] for e in entries if e["kind"] == "loan"}
    assert not loan_ids & {f"loan-{r.pk}" for r in permanent}


def test_overdue_returns_appear_today(it_client):
    workshop = AssetRequest.objects.get(title="Training workshop")
    AssetRequest.objects.filter(pk=workshop.pk).update(
        status=AssetRequestStatus.HANDED_OUT,
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


def test_calendar_shows_license_expiry(it_client):
    entries = fetch(it_client, kinds="license")
    assert [e["title"] for e in entries] == ["Autodesk AutoCAD LT"]
    assert entries[0]["link"]["name"] == "license"

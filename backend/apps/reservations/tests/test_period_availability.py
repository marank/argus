from datetime import date, timedelta

from apps.masterdata.models import Category


def _request_laptops(
    employee_client, it_client, start: date, days: int, quantity: int, pickup: date | None = None
) -> dict:
    laptops = Category.objects.get(code="laptops")
    reservation = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=days)).isoformat(),
            "requested_pickup_date": pickup.isoformat() if pickup else None,
            "items": [{"category": laptops.pk, "quantity": quantity}],
        },
        content_type="application/json",
    ).json()
    item_id = reservation["items"][0]["id"]
    it_client.post(
        f"/api/reservations/{reservation['id']}/confirm",
        {"items": [{"id": item_id, "quantity_confirmed": quantity}]},
        content_type="application/json",
    )
    return reservation


def _laptops(client, start: date, end: date) -> dict:
    counts = client.get(
        "/api/portal/availability", {"start": start.isoformat(), "end": end.isoformat()}
    ).json()
    return counts["categories"][str(Category.objects.get(code="laptops").pk)]


def test_confirmed_requests_reserve_their_period_only(employee_client, it_client):
    start = date.today() + timedelta(days=10)
    before = _laptops(it_client, start, start + timedelta(days=2))
    _request_laptops(employee_client, it_client, start, days=4, quantity=2)

    overlapping = _laptops(it_client, start + timedelta(days=3), start + timedelta(days=8))
    assert overlapping["reserved"] == before["reserved"] + 2
    assert overlapping["available"] == before["available"] - 2
    # Available and reserved together are what IT holds.
    assert overlapping["available"] + overlapping["reserved"] == before["available"] + before["reserved"]

    later = _laptops(it_client, start + timedelta(days=5), start + timedelta(days=8))
    assert later == before


def test_allocated_devices_stay_reserved_for_their_period(employee_client, it_client):
    start = date.today() + timedelta(days=10)
    before = _laptops(it_client, start, start)
    reservation = _request_laptops(employee_client, it_client, start, days=1, quantity=2)
    it_client.post(f"/api/reservations/{reservation['id']}/auto-allocate")

    assert _laptops(it_client, start, start)["reserved"] == before["reserved"] + 2
    # In another period the set-aside devices count as available again.
    later = start + timedelta(days=5)
    assert _laptops(it_client, later, later) == _laptops(
        it_client, start + timedelta(days=30), later + timedelta(days=30)
    )


def test_catalog_counts_follow_the_period(employee_client, it_client):
    start = date.today() + timedelta(days=10)
    _request_laptops(employee_client, it_client, start, days=1, quantity=1)
    laptops = str(Category.objects.get(code="laptops").pk)

    def catalog(**params):
        entries = it_client.get("/api/portal/catalog", params).json()
        return next(c for c in entries if c["id"] == laptops)

    inside = catalog(start=start.isoformat(), end=start.isoformat())
    outside = catalog(
        start=(start + timedelta(days=5)).isoformat(), end=(start + timedelta(days=6)).isoformat()
    )
    assert inside["reserved"] == outside["reserved"] + 1
    assert catalog(start=start.isoformat(), permanent="true")["reserved"] == inside["reserved"]


def test_availability_is_for_it_staff_only(employee_client):
    response = employee_client.get("/api/portal/availability", {"start": date.today().isoformat()})
    assert response.status_code in (401, 403)


def test_early_pickup_reserves_from_the_pickup_day(employee_client, it_client):
    start = date.today() + timedelta(days=10)
    pickup = start - timedelta(days=2)
    earlier = pickup - timedelta(days=1)
    before_pickup_day = _laptops(it_client, pickup, pickup)
    before_earlier = _laptops(it_client, earlier, earlier)
    _request_laptops(employee_client, it_client, start, days=1, quantity=2, pickup=pickup)

    # Taken from the pickup day on, not only from the day they are needed.
    assert _laptops(it_client, pickup, pickup)["reserved"] == before_pickup_day["reserved"] + 2
    assert _laptops(it_client, earlier, earlier) == before_earlier

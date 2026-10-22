from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Asset, AssetEvent
from apps.reservations.models import Reservation

URL = "/api/reservations/quick"
JSON = "application/json"


def in_stock() -> Asset:
    return Asset.objects.filter(status=Asset.Status.IN_STOCK).order_by("inventory_number").first()


def employee() -> User:
    return User.objects.get(username="employee")


def post(client, asset: Asset, **data):
    payload = {"asset": str(asset.pk), "requester": str(employee().pk), **data}
    return client.post(URL, payload, content_type=JSON)


def test_temporary_assignment_is_handed_out_with_its_return_date(it_client):
    asset = in_stock()
    until = timezone.localdate() + timedelta(days=5)
    response = post(it_client, asset, end_date=str(until))
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["origin"] == "quick"
    assert body["status"] == "handed_out"
    assert body["approval"] == ""
    assert body["end_date"] == until.isoformat()
    assert [e["kind"] for e in body["events"]] == ["quick", "handed_out"]
    assert body["events"][1]["data"]["items"] == [asset.inventory_number]

    asset.refresh_from_db()
    assert asset.status == Asset.Status.IN_USE
    assert asset.assigned_to == employee()
    # Straight from stock to the employee: no reservation step in between.
    kinds = list(asset.events.order_by("created_at").values_list("kind", flat=True))
    assert kinds[-1] == AssetEvent.Kind.ASSIGNED
    assert AssetEvent.Kind.RESERVED not in kinds
    assigned = asset.events.get(kind=AssetEvent.Kind.ASSIGNED, reservation_id=body["id"])
    assert assigned.related_user == employee()


def test_permanent_assignment_is_completed(it_client):
    asset = in_stock()
    body = post(it_client, asset, duration="permanent", end_date=str(timezone.localdate())).json()
    assert body["status"] == "completed"
    assert body["end_date"] is None


def test_earlier_start_dates_the_assignment_back(it_client):
    asset = in_stock()
    start = timezone.localdate() - timedelta(days=3)
    body = post(
        it_client, asset, start_date=str(start), end_date=str(timezone.localdate() + timedelta(days=1))
    ).json()
    assert body["start_date"] == start.isoformat()
    asset.refresh_from_db()
    assert timezone.localtime(asset.assigned_since).date() == start
    event = asset.events.get(kind=AssetEvent.Kind.ASSIGNED, reservation_id=body["id"])
    assert timezone.localtime(event.occurred_at).date() == start


def test_rejects_what_does_not_fit(it_client):
    asset = in_stock()
    today = timezone.localdate()
    assert post(it_client, asset).status_code == 409  # temporary without return date
    assert post(it_client, asset, end_date=str(today - timedelta(days=1))).status_code == 409
    assert (
        post(
            it_client,
            asset,
            start_date=str(today + timedelta(days=1)),
            end_date=str(today + timedelta(days=2)),
        ).status_code
        == 409
    )
    assert post(it_client, asset, duration="permanent").status_code == 201
    assert post(it_client, asset, duration="permanent").status_code == 409  # no longer in stock


def test_taking_back_on_the_device_page_completes_it(it_client):
    asset = in_stock()
    body = post(it_client, asset, end_date=str(timezone.localdate() + timedelta(days=2))).json()
    response = it_client.post(f"/api/inventory/assets/{asset.pk}/assign", {"user": None}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert Reservation.objects.get(pk=body["id"]).status == Reservation.Status.COMPLETED
    asset.refresh_from_db()
    assert asset.status == Asset.Status.IN_STOCK
    assert asset.events.filter(kind=AssetEvent.Kind.RETURNED, reservation_id=body["id"]).count() == 1


def test_employees_cannot(employee_client):
    asset = in_stock()
    response = post(employee_client, asset, duration="permanent")
    assert response.status_code == 403

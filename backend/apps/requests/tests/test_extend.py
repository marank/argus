from datetime import timedelta

from django.utils import timezone

from apps.requests.models import AssetRequest

from .flow import JSON, handed_out, laptops, prepare


def extend(client, rid, end):
    return client.post(f"/api/requests/{rid}/extend", {"end_date": end.isoformat()}, content_type=JSON)


def test_extend_moves_the_return_date(employee_client, it_client):
    rid = handed_out(employee_client, it_client)
    end_date = AssetRequest.objects.get(pk=rid).end_date
    assert end_date is not None
    new_end = end_date + timedelta(days=60)
    response = extend(it_client, rid, new_end)
    assert response.status_code == 200, response.content
    data = response.json()
    assert data["end_date"] == new_end.isoformat()
    assert data["status"] == "handed_out"
    assert data["handled_by"]["username"] == "it"


def test_extend_turns_an_overdue_return_into_a_current_one(employee_client, it_client):
    rid = handed_out(employee_client, it_client)
    AssetRequest.objects.filter(pk=rid).update(end_date=timezone.localdate() - timedelta(days=3))
    assert it_client.get(f"/api/requests/{rid}").json()["is_overdue"]
    response = extend(it_client, rid, timezone.localdate())
    assert response.status_code == 200, response.content
    assert not response.json()["is_overdue"]


def test_extend_rejects_earlier_or_past_dates(employee_client, it_client):
    rid = handed_out(employee_client, it_client)
    end = AssetRequest.objects.get(pk=rid).end_date
    assert extend(it_client, rid, end).status_code == 409
    assert extend(it_client, rid, timezone.localdate() - timedelta(days=1)).status_code == 409


def test_extend_needs_a_temporary_handed_out_request(employee_client, it_client):
    rid = prepare(employee_client, it_client, laptops())
    assert extend(it_client, rid, timezone.localdate() + timedelta(days=30)).status_code == 409
    rid = handed_out(employee_client, it_client, duration="permanent")
    assert extend(it_client, rid, timezone.localdate() + timedelta(days=30)).status_code == 409

from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.reservations.models import Reservation


def test_overdue_returns_list_lent_devices_past_their_date(it_client):
    workshop = Reservation.objects.get(title="Training workshop")
    Reservation.objects.filter(pk=workshop.pk).update(
        status=Reservation.Status.HANDED_OUT,
        duration=Reservation.Duration.TEMPORARY,
        end_date=timezone.localdate() - timedelta(days=3),
    )
    rows = it_client.get("/api/dashboard/widgets/overdue-returns").json()
    row = next(r for r in rows if r["id"] == str(workshop.pk))
    assert row["can_remind"] is bool(workshop.requester.email)
    assert row["reminded_at"] is None


def test_my_tasks_and_team_load_follow_the_assignee(it_client):
    me = User.objects.get(username="it")
    workshop = Reservation.objects.get(title="Training workshop")
    Reservation.objects.filter(pk=workshop.pk).update(status=Reservation.Status.SUBMITTED, assignee=me)

    tasks = it_client.get("/api/dashboard/widgets/my-tasks").json()
    assert str(workshop.pk) in {r["id"] for r in tasks["requests"]}
    assert tasks["requests_total"] >= 1

    load = it_client.get("/api/dashboard/widgets/team-load").json()
    mine = next(p for p in load["people"] if p["user"]["username"] == "it")
    assert mine["requests"] >= 1


def test_request_trend_counts_this_weeks_requests(it_client):
    before = it_client.get("/api/dashboard/widgets/request-trend").json()[-1]["created"]
    workshop = Reservation.objects.get(title="Training workshop")
    workshop.pk, workshop.number = None, ""
    workshop.save()
    weeks = it_client.get("/api/dashboard/widgets/request-trend").json()
    monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
    assert weeks[-1]["week_start"] == monday.isoformat()
    assert weeks[-1]["created"] == before + 1

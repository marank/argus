from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.requests.models import AssetRequest, AssetRequestStatus


def test_overdue_returns_list_lent_devices_past_their_date(it_client):
    workshop = AssetRequest.objects.get(title="Training workshop")
    AssetRequest.objects.filter(pk=workshop.pk).update(
        status=AssetRequestStatus.HANDED_OUT,
        duration=AssetRequest.Duration.TEMPORARY,
        end_date=timezone.localdate() - timedelta(days=3),
    )
    rows = it_client.get("/api/dashboard/widgets/overdue-returns").json()
    row = next(r for r in rows if r["id"] == str(workshop.pk))
    assert row["can_remind"] is bool(workshop.requester.email)
    assert row["reminded_at"] is None


def test_my_tasks_and_team_load_follow_the_assignee(it_client):
    me = User.objects.get(username="it")
    workshop = AssetRequest.objects.get(title="Training workshop")
    AssetRequest.objects.filter(pk=workshop.pk).update(status=AssetRequestStatus.SUBMITTED, assignee=me)

    tasks = it_client.get("/api/dashboard/widgets/my-tasks").json()
    assert str(workshop.pk) in {r["id"] for r in tasks["requests"]}
    assert tasks["requests_total"] >= 1

    load = it_client.get("/api/dashboard/widgets/team-load").json()
    mine = next(p for p in load["people"] if p["user"]["username"] == "it")
    assert mine["requests"] >= 1


def test_request_trend_counts_this_weeks_requests(it_client):
    before = it_client.get("/api/dashboard/widgets/request-trend").json()[-1]["created"]
    workshop = AssetRequest.objects.get(title="Training workshop")
    workshop.pk, workshop.number = None, ""
    workshop.save()
    weeks = it_client.get("/api/dashboard/widgets/request-trend").json()
    monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
    assert weeks[-1]["week_start"] == monday.isoformat()
    assert weeks[-1]["created"] == before + 1


def test_upcoming_follows_the_chosen_period(it_client):
    workshop = AssetRequest.objects.get(title="Training workshop")
    AssetRequest.objects.filter(pk=workshop.pk).update(
        status=AssetRequestStatus.CONFIRMED, start_date=timezone.localdate() + timedelta(days=10)
    )
    week = {r["id"] for r in it_client.get("/api/dashboard/widgets/upcoming?days=7").json()}
    fortnight = {r["id"] for r in it_client.get("/api/dashboard/widgets/upcoming?days=14").json()}
    assert str(workshop.pk) not in week
    assert str(workshop.pk) in fortnight
    assert it_client.get("/api/dashboard/widgets/upcoming?days=40").status_code == 422


def test_upcoming_includes_requests_not_confirmed_yet(it_client):
    count = AssetRequest.objects.get(title="Inventory count in the warehouse")
    assert count.status == AssetRequestStatus.SUBMITTED
    rows = it_client.get("/api/dashboard/widgets/upcoming?days=7").json()
    row = next(r for r in rows if r["id"] == str(count.pk))
    assert row["status"] == "submitted"


def test_due_returns_list_lent_devices_due_soon_but_not_overdue(it_client):
    workshop = AssetRequest.objects.get(title="Training workshop")
    lent = AssetRequest.objects.filter(pk=workshop.pk)
    lent.update(status=AssetRequestStatus.HANDED_OUT, duration=AssetRequest.Duration.TEMPORARY)

    def listed():
        rows = it_client.get("/api/dashboard/widgets/due-returns").json()
        return str(workshop.pk) in {r["id"] for r in rows}

    lent.update(end_date=timezone.localdate() + timedelta(days=2))
    assert listed()
    lent.update(end_date=timezone.localdate() - timedelta(days=1))
    assert not listed()


def test_waiting_requests_list_submitted_requests(it_client):
    workshop = AssetRequest.objects.get(title="Training workshop")
    AssetRequest.objects.filter(pk=workshop.pk).update(status=AssetRequestStatus.SUBMITTED)
    rows = it_client.get("/api/dashboard/widgets/waiting-requests").json()
    assert str(workshop.pk) in {r["id"] for r in rows}
    assert [r["created_at"] for r in rows] == sorted(r["created_at"] for r in rows)


def test_list_widgets_answer(it_client):
    for path in ("expiring", "low-stock", "open-orders"):
        assert it_client.get(f"/api/dashboard/widgets/{path}").status_code == 200

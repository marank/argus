"""The page "Activities" and the dashboard show only the areas a user may read."""

from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tests.test_roles import grant, staff, staff_client  # noqa: F401 - fixtures
from apps.activity.models import Activity, ActivityKind
from apps.activity.services.log import log

URL = "/api/activities"


def add(kind: ActivityKind, label: str, days_ago: int = 0) -> Activity:
    row = log(kind, None, label, User.objects.get(username="it"))
    assert row is not None
    Activity.objects.filter(pk=row.pk).update(occurred_at=timezone.now() - timedelta(days=days_ago))
    return row


def labels(response) -> list[str]:
    assert response.status_code == 200, response.content
    return [row["subject_label"] for row in response.json()["items"]]


def test_list_filters_and_searches(it_client, fresh):
    add(ActivityKind.ASSET_NOTE, "MDE-0001", days_ago=3)
    add(ActivityKind.ORDER_PLACED, "PO-1", days_ago=1)
    add(ActivityKind.REQUEST_HANDED_OUT, "REQ-1")

    assert labels(it_client.get(URL)) == ["REQ-1", "PO-1", "MDE-0001"]
    assert labels(it_client.get(f"{URL}?area=procurement&area=assets")) == ["PO-1", "MDE-0001"]
    assert labels(it_client.get(f"{URL}?kind=request_handed_out")) == ["REQ-1"]
    since = (timezone.localdate() - timedelta(days=2)).isoformat()
    assert labels(it_client.get(f"{URL}?since={since}")) == ["REQ-1", "PO-1"]
    assert labels(it_client.get(f"{URL}?q=mde")) == ["MDE-0001"]
    assert labels(it_client.get(f"{URL}?ordering=occurred_at")) == ["MDE-0001", "PO-1", "REQ-1"]


def test_rows_follow_the_right_to_read_the_area(staff, staff_client, fresh):  # noqa: F811
    add(ActivityKind.ASSET_NOTE, "MDE-0001")
    add(ActivityKind.ORDER_PLACED, "PO-1")
    assert labels(staff_client.get(URL)) == []
    assert staff_client.get("/api/dashboard/it").json()["recent_events"] == []

    grant(staff, assets="read")
    assert labels(staff_client.get(URL)) == ["MDE-0001"]
    recent = staff_client.get("/api/dashboard/it").json()["recent_events"]
    assert [row["subject_label"] for row in recent] == ["MDE-0001"]
    assert recent[0]["actor"]["username"] == "it"


def test_employees_have_no_access(employee_client, fresh):
    assert employee_client.get(URL).status_code in (401, 403)


def test_muted_writes_nothing(fresh):
    from apps.activity.services.log import muted

    with muted():
        assert log(ActivityKind.ASSET_NOTE, None, "MDE-0001") is None
    assert not Activity.objects.exists()

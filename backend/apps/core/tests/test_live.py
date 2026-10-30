import pytest

from apps.accounts.models import User
from apps.core import live
from apps.inventory.models import Asset, AssetIssueKind
from apps.inventory.services.issues import report_issue

from .test_notifications import submit


@pytest.fixture
def signals(settings, monkeypatch):
    """Live update signals published in a test (PostgreSQL's NOTIFY is not available on SQLite)."""
    settings.LIVE_EVENTS = True
    sent = []
    monkeypatch.setattr(
        live,
        "publish",
        lambda topic, id=None, *, users=(), staff=True: sent.append(
            (topic, str(id), {str(user) for user in users if user})
        ),
    )
    return sent


def test_a_new_request_signals_its_requester(demo, employee_client, signals):
    asset_request = submit(employee_client).json()
    employee = User.objects.get(username="employee")
    assert ("request", asset_request["id"], {str(employee.pk)}) in signals


def test_a_problem_report_signals_its_reporter(demo, signals):
    employee = User.objects.get(username="employee")
    asset = Asset.objects.first()
    assert asset is not None
    issue = report_issue(asset, employee, AssetIssueKind.DEFECT, "Display flickers")
    assert ("issue", str(issue.pk), {str(employee.pk)}) in signals


def test_signals_reach_it_and_the_named_users_only():
    event: live.Event = {"topic": "issue", "id": "1", "users": ["u1"], "staff": True}
    assert live.visible_to(event, "u1", is_staff=False)
    assert live.visible_to(event, "u2", is_staff=True)
    assert not live.visible_to(event, "u2", is_staff=False)
    assert not live.visible_to({**event, "staff": False}, "u2", is_staff=True)


def test_nothing_is_published_without_postgresql(demo, settings, django_assert_num_queries):
    settings.LIVE_EVENTS = False
    with django_assert_num_queries(0):
        live.publish("request", "r1")

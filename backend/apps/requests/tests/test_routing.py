from datetime import date, timedelta
from typing import Any

import pytest
from django.core import mail

from apps.accounts.models import Team, User
from apps.core.models import MailSettings
from apps.inventory.models import Asset, AssetIssue
from apps.masterdata.models import AssetModel, Category
from apps.requests.models import AssetRequest

JSON = "application/json"


@pytest.fixture
def mail_on(demo):
    settings = MailSettings.load()
    settings.enabled = True
    settings.host = "smtp.example.com"
    settings.from_email = "argus@example.com"
    settings.save()


@pytest.fixture
def staff(demo) -> dict[str, User]:
    it = User.objects.get(username="it")
    other = User.objects.create_user(
        "nav", email="nav@example.com", is_staff=True, first_name="Nora", last_name="Nav"
    )
    return {"it": it, "nav": other}


def submit(client, item: dict[str, Any]) -> dict[str, Any]:
    start = date.today() + timedelta(days=2)
    response = client.post(
        "/api/requests",
        {
            "title": "Routing",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=2)).isoformat(),
            "items": [{"quantity": 1, **item}],
        },
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    body: dict[str, Any] = response.json()
    return body


def team_of(asset_request: dict[str, Any]) -> Team | None:
    return AssetRequest.objects.get(pk=asset_request["id"]).assigned_team


def test_requests_route_by_model_then_category_then_default(employee_client, demo):
    laptop = AssetModel.objects.filter(category__code="laptops").first()
    assert laptop is not None
    support = Team.objects.create(name="IT-Support", is_default=True)
    hardware = Team.objects.create(name="Hardware")
    special = Team.objects.create(name="Special")

    # Nothing set on model or category: the default team.
    assert team_of(submit(employee_client, {"asset_model": str(laptop.pk)})) == support

    # Inherited from a parent category.
    root = laptop.category
    while root.parent is not None:
        root = root.parent
    root.team = hardware
    root.save()
    assert team_of(submit(employee_client, {"category": str(laptop.category_id)})) == hardware

    # The model's own team wins over its category.
    laptop.team = special
    laptop.save()
    assert team_of(submit(employee_client, {"asset_model": str(laptop.pk)})) == special


def test_without_any_team_requests_stay_unassigned(employee_client, demo):
    laptops = Category.objects.get(code="laptops")
    assert team_of(submit(employee_client, {"category": str(laptops.pk)})) is None


def test_only_one_default_team(demo):
    first = Team.objects.create(name="First", is_default=True)
    Team.objects.create(name="Second", is_default=True)
    first.refresh_from_db()
    assert not first.is_default
    assert Team.objects.filter(is_default=True).count() == 1


def test_new_request_notifies_only_the_routed_team(
    mail_on, staff, employee_client, django_capture_on_commit_callbacks
):
    ledgerline = Team.objects.create(name="Ledgerline", is_default=True)
    ledgerline.members.add(staff["nav"])
    laptops = Category.objects.get(code="laptops")
    with django_capture_on_commit_callbacks(execute=True):
        submit(employee_client, {"category": str(laptops.pk)})
    assert {a for m in mail.outbox for a in m.to} == {"nav@example.com"}


def test_team_without_it_members_falls_back_to_all_of_it(
    mail_on, staff, employee_client, django_capture_on_commit_callbacks
):
    Team.objects.create(name="Empty", is_default=True)
    laptops = Category.objects.get(code="laptops")
    with django_capture_on_commit_callbacks(execute=True):
        submit(employee_client, {"category": str(laptops.pk)})
    assert "nav@example.com" in {a for m in mail.outbox for a in m.to}
    assert len(mail.outbox) > 1


def test_reports_route_and_notify_the_team(
    mail_on, staff, employee_client, django_capture_on_commit_callbacks
):
    ledgerline = Team.objects.create(name="Ledgerline", is_default=True)
    ledgerline.members.add(staff["nav"])
    asset = Asset.objects.filter(assigned_to__username="employee").first()
    assert asset is not None
    with django_capture_on_commit_callbacks(execute=True):
        response = employee_client.post(
            f"/api/portal/my-assets/{asset.pk}/issues",
            {"kind": "defect", "description": "Broken"},
            content_type=JSON,
        )
    assert response.status_code in (200, 201), response.content
    assert AssetIssue.objects.get(asset=asset).assigned_team == ledgerline
    assert {a for m in mail.outbox for a in m.to} == {"nav@example.com"}


def test_assignee_hears_of_it_but_not_when_taking_it_themselves(
    mail_on, staff, it_client, django_capture_on_commit_callbacks
):
    asset_request = AssetRequest.objects.first()
    assert asset_request is not None
    url = f"/api/requests/{asset_request.pk}/assign"
    with django_capture_on_commit_callbacks(execute=True):
        it_client.post(url, {"assignee": str(staff["nav"].pk)}, content_type=JSON)
    assert [m.to for m in mail.outbox] == [["nav@example.com"]]
    assert asset_request.number in mail.outbox[0].subject

    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        # Unchanged assignee: no second mail; assigning oneself: none either.
        it_client.post(url, {"assignee": str(staff["nav"].pk)}, content_type=JSON)
        it_client.post(url, {"assignee": str(staff["it"].pk)}, content_type=JSON)
    assert mail.outbox == []

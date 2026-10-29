from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Team, User
from apps.inventory.models import Asset, AssetIssue
from apps.requests.models import AssetRequest


@pytest.fixture
def support(demo) -> Team:
    team = Team.objects.create(name="IT-Support")
    team.members.add(User.objects.get(username="it"))
    return team


def _assign(client, asset_request, **payload):
    return client.post(f"/api/requests/{asset_request.pk}/assign", payload, content_type="application/json")


def test_team_and_assignee_are_independent(it_client, support):
    asset_request = AssetRequest.objects.first()
    it = User.objects.get(username="it")

    response = _assign(it_client, asset_request, team=str(support.pk))
    assert response.status_code == 200, response.content
    assert response.json()["assigned_team"]["name"] == "IT-Support"
    assert response.json()["assignee"] is None

    # A person without a team stays without a team.
    response = _assign(it_client, asset_request, assignee=str(it.pk))
    assert response.json()["assigned_team"] is None
    assert response.json()["assignee"]["username"] == "it"

    response = _assign(it_client, asset_request)
    assert response.json()["assigned_team"] is None and response.json()["assignee"] is None


def test_only_it_staff_can_be_assigned(it_client, demo):
    asset_request = AssetRequest.objects.first()
    assert asset_request is not None
    employee = User.objects.get(username="employee")
    response = _assign(it_client, asset_request, assignee=str(employee.pk))
    assert response.status_code == 409
    asset_request.refresh_from_db()
    assert asset_request.assignee is None


def test_employees_can_neither_assign_nor_see_it(employee_client, support):
    asset_request = AssetRequest.objects.filter(requester__username="employee").first()
    assert asset_request is not None
    assert _assign(employee_client, asset_request, team=str(support.pk)).status_code == 403

    asset_request.assigned_team = support
    asset_request.assignee = User.objects.get(username="it")
    asset_request.save()
    detail = employee_client.get(f"/api/requests/{asset_request.pk}").json()
    assert detail["assigned_team"] is None and detail["assignee"] is None
    listed = employee_client.get("/api/requests").json()["items"]
    assert all(r["assigned_team"] is None and r["assignee"] is None for r in listed)
    assert employee_client.get("/api/accounts/teams").status_code == 403


def test_assignment_filters(it_client, support):
    it = User.objects.get(username="it")
    mine, team_only, other_team, unassigned = AssetRequest.objects.all()[:4]
    mine.assignee = it
    mine.save()
    team_only.assigned_team = support
    team_only.save()
    other_team.assigned_team = Team.objects.create(name="Ledgerline")
    other_team.save()

    def ids(**params):
        return {r["id"] for r in it_client.get("/api/requests", params).json()["items"]}

    assert ids(assigned="me") == {str(mine.pk)}
    assert ids(assigned="my_teams") == {str(mine.pk), str(team_only.pk)}
    assert str(unassigned.pk) in ids(assigned="nobody")
    assert not {str(mine.pk), str(team_only.pk), str(other_team.pk)} & ids(assigned="nobody")
    assert ids(team=[str(support.pk), str(other_team.assigned_team_id)]) == {
        str(team_only.pk),
        str(other_team.pk),
    }
    assert ids(assignee=str(it.pk)) == {str(mine.pk)}


def test_team_crud_with_members(it_client, demo):
    it = User.objects.get(username="it")
    response = it_client.post(
        "/api/accounts/teams",
        {"name": "Ledgerline", "code": "LDG", "members": [str(it.pk)]},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content
    assert [m["username"] for m in response.json()["members"]] == ["it"]
    listed = it_client.get("/api/accounts/teams", {"member": str(it.pk)}).json()["items"]
    assert [t["name"] for t in listed] == ["Ledgerline"]


def test_issues_can_be_assigned_and_filtered(it_client, support):
    it = User.objects.get(username="it")
    asset = Asset.objects.first()
    assert asset is not None
    mine = AssetIssue.objects.create(asset=asset, description="Screen broken")
    other = AssetIssue.objects.create(asset=asset, description="Battery dead")

    response = it_client.post(
        f"/api/inventory/issues/{mine.pk}/assign",
        {"team": str(support.pk), "assignee": str(it.pk)},
        content_type="application/json",
    )
    assert response.status_code == 200, response.content
    assert response.json()["assigned_team"]["name"] == "IT-Support"
    assert response.json()["assignee"]["username"] == "it"

    def ids(**params):
        return {i["id"] for i in it_client.get("/api/inventory/issues", params).json()["items"]}

    assert ids(assigned="me") == {str(mine.pk)}
    assert ids(team=[str(support.pk)]) == {str(mine.pk)}
    assert str(other.pk) in ids(assigned="nobody")


def test_dashboard_counts_the_users_queue(it_client, support):
    it = User.objects.get(username="it")
    open_requests = AssetRequest.objects.filter(status__in=AssetRequest.OPEN_STATUSES)
    first, second = open_requests[:2]
    first.assignee = it
    first.save()
    second.assigned_team = support
    second.save()
    asset = Asset.objects.first()
    assert asset is not None
    AssetIssue.objects.create(asset=asset, description="Broken", assignee=it)

    data = it_client.get("/api/dashboard/it").json()
    assert data["requests_mine"] == 1
    assert data["requests_my_teams"] == 2
    assert data["requests_unassigned"] == open_requests.count() - 2
    assert data["issues_mine"] == 1


def test_calendar_narrows_requests_to_the_users_queue(it_client, support):
    workshop = AssetRequest.objects.get(title="Training workshop")
    today = timezone.localdate()
    query = {
        "start": (today - timedelta(days=10)).isoformat(),
        "end": (today + timedelta(days=40)).isoformat(),
    }

    def request_ids(**params):
        entries = it_client.get("/api/calendar", {**query, **params}).json()
        return {e["link"]["id"] for e in entries if e["kind"] in ("loan", "pickup", "return")}

    assert str(workshop.pk) in request_ids()
    assert request_ids(assigned="me") == set()
    workshop.assigned_team = support
    workshop.save()
    assert request_ids(assigned="my_teams") == {str(workshop.pk)}

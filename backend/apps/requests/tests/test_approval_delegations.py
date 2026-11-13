from datetime import timedelta

import pytest
from django.core import mail
from django.test import Client
from django.utils import timezone

from apps.accounts.models import ApprovalDelegation, Department, User
from apps.requests.tests.test_approvals import approval_setup, approver_client, request

__all__ = ["approval_setup", "approver_client"]

JSON = "application/json"


@pytest.fixture(autouse=True)
def anna(demo) -> User:
    """A colleague of the approver who stands in for them."""
    return User.objects.create_user(
        "abecker", "abecker@example.com", "argus-demo", first_name="Anna", last_name="Becker"
    )


def client_for(username: str) -> Client:
    client = Client()
    client.force_login(User.objects.get(username=username))
    return client


def delegate_to(client: Client, username: str, start_in: int = 0, days: int | None = 7):
    start = timezone.localdate() + timedelta(days=start_in)
    payload = {
        "delegate": str(User.objects.get(username=username).pk),
        "starts_on": start.isoformat(),
        "ends_on": (start + timedelta(days=days)).isoformat() if days is not None else None,
    }
    return client.post("/api/approvals/delegations", payload, content_type=JSON)


def test_approver_names_a_delegate_who_then_decides(
    approver_client, employee_client, django_capture_on_commit_callbacks
):
    response = delegate_to(approver_client, "abecker")
    assert response.status_code == 201, response.content
    assert response.json()["delegate"]["username"] == "abecker"

    delegate = client_for("abecker")
    assert delegate.get("/api/auth/me").json()["is_approver"] is True
    assert delegate.get("/api/auth/me").json()["is_department_approver"] is False
    standing_in = delegate.get("/api/approvals/delegations").json()["received"]
    assert [d["approver"]["username"] for d in standing_in] == ["sales"]

    with django_capture_on_commit_callbacks(execute=True):
        asset_request = request(employee_client, "laptops")
    assert sorted(a["username"] for a in asset_request["approvers"]) == ["abecker", "sales"]
    assert "abecker@example.com" in [to for m in mail.outbox for to in m.to]

    assert [r["id"] for r in delegate.get("/api/approvals").json()["items"]] == [asset_request["id"]]
    approved = delegate.post(f"/api/approvals/{asset_request['id']}/approve", {}, content_type=JSON)
    assert approved.status_code == 200, approved.content
    assert approved.json()["approver"]["username"] == "abecker"


def test_delegate_decides_only_while_the_period_runs(approver_client, employee_client):
    assert delegate_to(approver_client, "abecker", start_in=3).status_code == 201
    asset_request = request(employee_client, "laptops")
    delegate = client_for("abecker")
    assert delegate.get("/api/approvals").json()["items"] == []
    response = delegate.post(f"/api/approvals/{asset_request['id']}/approve", {}, content_type=JSON)
    assert response.status_code == 404
    assert delegate.get("/api/auth/me").json()["is_approver"] is False

    # Without an end the delegate stands in until removed.
    ApprovalDelegation.objects.update(starts_on=timezone.localdate(), ends_on=None)
    assert [r["id"] for r in delegate.get("/api/approvals").json()["items"]] == [asset_request["id"]]


def test_delegates_own_request_still_needs_approval(approver_client):
    delegate_user = User.objects.get(username="abecker")
    delegate_user.department = Department.objects.get(name="Logistics")
    delegate_user.save()
    assert delegate_to(approver_client, "abecker").status_code == 201
    own = request(client_for("abecker"), "laptops")
    assert own["status"] == "pending_approval"


def test_only_department_approvers_name_delegations(approval_setup, employee_client):
    assert delegate_to(employee_client, "abecker").status_code == 403
    assert employee_client.get("/api/approvals/delegations/candidates?q=be").status_code == 403


def test_rules_for_naming_a_delegate(approver_client):
    assert delegate_to(approver_client, "sales").status_code == 422
    assert delegate_to(approver_client, "abecker", start_in=-1).status_code == 422
    assert delegate_to(approver_client, "abecker", days=-2).status_code == 422
    assert delegate_to(approver_client, "terminal").status_code == 422
    assert not ApprovalDelegation.objects.exists()


def test_approver_removes_own_delegations_only(approver_client):
    entry = delegate_to(approver_client, "abecker").json()
    assert client_for("abecker").delete(f"/api/approvals/delegations/{entry['id']}").status_code == 404
    assert approver_client.delete(f"/api/approvals/delegations/{entry['id']}").status_code == 204
    assert approver_client.get("/api/approvals/delegations").json()["mine"] == []


def test_candidates_leave_out_the_approver_and_terminals(approver_client):
    assert approver_client.get("/api/approvals/delegations/candidates?q=b").json() == []
    names = [u["username"] for u in approver_client.get("/api/approvals/delegations/candidates?q=be").json()]
    assert "abecker" in names
    assert "sales" not in names
    terminals = approver_client.get("/api/approvals/delegations/candidates?q=terminal").json()
    assert terminals == []


def test_page_lists_departments_status_and_history(approver_client):
    planned = delegate_to(approver_client, "abecker", start_in=3).json()
    assert planned["status"] == "planned"
    running = delegate_to(approver_client, "abecker").json()
    assert running["status"] == "running"
    yesterday = timezone.localdate() - timedelta(days=1)
    old = ApprovalDelegation.objects.create(
        approver=User.objects.get(username="sales"),
        delegate=User.objects.get(username="abecker"),
        starts_on=yesterday - timedelta(days=5),
        ends_on=yesterday,
    )
    data = approver_client.get("/api/approvals/delegations").json()
    assert [d["name"] for d in data["departments"]] == ["Logistics"]
    assert [d["status"] for d in data["mine"]] == ["running", "planned"]
    assert [d["id"] for d in data["past"]] == [str(old.pk)]


def test_period_changes_follow_the_rules(approver_client):
    today = timezone.localdate()
    running = delegate_to(approver_client, "abecker").json()
    url = f"/api/approvals/delegations/{running['id']}"
    longer = {"starts_on": today.isoformat(), "ends_on": (today + timedelta(days=20)).isoformat()}
    assert approver_client.put(url, longer, content_type=JSON).json()["ends_on"] == longer["ends_on"]
    moved = {**longer, "starts_on": (today + timedelta(days=1)).isoformat()}
    assert approver_client.put(url, moved, content_type=JSON).status_code == 422
    past_end = {**longer, "ends_on": (today - timedelta(days=1)).isoformat()}
    assert approver_client.put(url, past_end, content_type=JSON).status_code == 422
    assert client_for("abecker").put(url, longer, content_type=JSON).status_code == 404


def test_back_early_ends_a_running_delegate_and_drops_a_planned_one(approver_client):
    started = ApprovalDelegation.objects.create(
        approver=User.objects.get(username="sales"),
        delegate=User.objects.get(username="abecker"),
        starts_on=timezone.localdate() - timedelta(days=2),
    )
    planned = delegate_to(approver_client, "abecker", start_in=5).json()
    assert approver_client.post(f"/api/approvals/delegations/{started.pk}/end").status_code == 204
    started.refresh_from_db()
    assert started.ends_on == timezone.localdate() - timedelta(days=1)
    assert client_for("abecker").get("/api/auth/me").json()["is_approver"] is False
    assert approver_client.post(f"/api/approvals/delegations/{planned['id']}/end").status_code == 204
    assert not ApprovalDelegation.objects.filter(pk=planned["id"]).exists()

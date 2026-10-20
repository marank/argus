from datetime import date, timedelta

import pytest
from django.core import mail
from django.test import Client

from apps.accounts.models import Department, User
from apps.core.models import MailSettings
from apps.masterdata.models import Category
from apps.reservations.models import Reservation

JSON = "application/json"


@pytest.fixture
def approval_setup(demo):
    """Laptops need approval; Sam from Sales approves for Logistics, where Erika works."""
    Category.objects.filter(code="laptops").update(requires_approval=True)
    approver = User.objects.get(username="sales")
    Department.objects.get(name="Logistics").approvers.add(approver)
    settings = MailSettings.load()
    settings.enabled, settings.host, settings.from_email = True, "smtp.example.com", "argus@example.com"
    settings.app_url = "https://argus.example.com"
    settings.save()
    return approver


@pytest.fixture
def approver_client(approval_setup) -> Client:
    client = Client()
    client.login(username="sales", password="argus-demo")
    return client


def request(client, *categories: str, requester: User | None = None) -> dict:
    start = date.today() + timedelta(days=3)
    payload = {
        "title": "Workshop",
        "duration": "temporary",
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=2)).isoformat(),
        "items": [
            {"category": str(Category.objects.get(code=code).pk), "quantity": 1} for code in categories
        ],
    }
    if requester:
        payload["requester"] = str(requester.pk)
    response = client.post("/api/reservations", payload, content_type=JSON)
    assert response.status_code == 201, response.content
    return response.json()


def test_request_waits_for_the_department_then_goes_to_it(
    approval_setup, employee_client, approver_client, it_client, django_capture_on_commit_callbacks
):
    # Mixed request: the headset alone would not need approval, the laptop does.
    with django_capture_on_commit_callbacks(execute=True):
        reservation = request(employee_client, "laptops", "headsets")
    assert reservation["status"] == "pending_approval"
    assert reservation["approval"] == "pending"
    assert [a["username"] for a in reservation["approvers"]] == ["sales"]
    assert [m.to for m in mail.outbox] == [["sales@example.com"]]
    assert "/portal/approvals/" in mail.outbox[0].body

    # IT sees it, but cannot act on it yet.
    url = f"/api/reservations/{reservation['id']}"
    assert it_client.get(url).json()["status"] == "pending_approval"
    assert it_client.post(f"{url}/confirm", {"items": []}, content_type=JSON).status_code == 409

    pending = approver_client.get("/api/approvals").json()["items"]
    assert [r["id"] for r in pending] == [reservation["id"]]
    assert approver_client.get(url).json()["can_approve"] is True

    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        response = approver_client.post(
            f"/api/approvals/{reservation['id']}/approve", {"comment": "Fine"}, content_type=JSON
        )
    assert response.status_code == 200, response.content
    approved = response.json()
    assert approved["status"] == "submitted"
    assert approved["approval"] == "approved"
    assert approved["approver"]["username"] == "sales"
    assert approved["approval_comment"] == "Fine"
    assert approved["can_approve"] is False
    # Now IT gets the request as work.
    assert "it@example.com" in [to for m in mail.outbox for to in m.to]

    # Decided: done for the approver, it leaves the list.
    assert approver_client.get("/api/approvals").json()["items"] == []
    assert it_client.post(f"{url}/confirm", {"items": []}, content_type=JSON).status_code == 200
    # Opened again, the approver sees the request and the decision, not IT's work after it.
    events = approver_client.get(url).json()["events"]
    assert [e["kind"] for e in events] == ["created", "approved"]


def test_declined_request_is_closed_with_the_comment(
    approval_setup, employee_client, approver_client, django_capture_on_commit_callbacks
):
    reservation = request(employee_client, "laptops")
    base = f"/api/approvals/{reservation['id']}"
    assert approver_client.post(f"{base}/decline", {"comment": ""}, content_type=JSON).status_code == 422

    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True):
        response = approver_client.post(f"{base}/decline", {"comment": "Not in budget"}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "rejected"
    assert response.json()["approval"] == "rejected"
    assert [m.to for m in mail.outbox] == [["employee@example.com"]]
    assert "Not in budget" in mail.outbox[0].body

    assert approver_client.post(f"{base}/approve", {}, content_type=JSON).status_code == 409


def test_only_the_departments_approvers_decide(approval_setup, employee_client, it_client):
    reservation = request(employee_client, "laptops")
    url = f"/api/reservations/{reservation['id']}"
    # The requester sees the request, but does not decide on it.
    assert employee_client.get(url).json()["can_approve"] is False
    response = employee_client.post(f"/api/approvals/{reservation['id']}/approve", {}, content_type=JSON)
    assert response.status_code == 409
    # IT staff are no approvers either.
    response = it_client.post(f"/api/approvals/{reservation['id']}/approve", {}, content_type=JSON)
    assert response.status_code == 409

    # Approvers of another department neither see nor decide it.
    other = Client()
    other.login(username="sales", password="argus-demo")
    Department.objects.get(name="Logistics").approvers.clear()
    Department.objects.get(name="Sales").approvers.add(User.objects.get(username="sales"))
    assert other.get(url).status_code == 404
    assert other.get("/api/approvals").json()["items"] == []


def test_employees_cancel_while_waiting(approval_setup, employee_client, approver_client):
    reservation = request(employee_client, "laptops")
    response = employee_client.post(f"/api/reservations/{reservation['id']}/cancel")
    assert response.json()["status"] == "cancelled"
    assert approver_client.get("/api/approvals").json()["items"] == []
    response = approver_client.post(f"/api/approvals/{reservation['id']}/approve", {}, content_type=JSON)
    assert response.status_code == 409


def test_requests_that_go_straight_to_it(approval_setup, employee_client, approver_client, it_client):
    # Nothing that needs approval.
    assert request(employee_client, "headsets")["status"] == "submitted"

    # Requests IT records on someone's behalf.
    employee = User.objects.get(username="employee")
    on_behalf = request(it_client, "laptops", requester=employee)
    assert (on_behalf["status"], on_behalf["approval"]) == ("submitted", "")

    # Exempt employees.
    User.objects.filter(pk=employee.pk).update(approval_exempt=True)
    assert request(employee_client, "laptops")["status"] == "submitted"
    User.objects.filter(pk=employee.pk).update(approval_exempt=False)

    # Departments without approvers.
    Department.objects.get(name="Logistics").approvers.clear()
    assert request(employee_client, "laptops")["status"] == "submitted"


def test_approvers_own_requests_are_approved_right_away(approval_setup, approver_client):
    approver = approval_setup
    approver.department = Department.objects.get(name="Logistics")
    approver.save()
    reservation = request(approver_client, "laptops")
    assert reservation["status"] == "submitted"
    assert reservation["approval"] == "approved"
    assert reservation["approver"]["username"] == "sales"


def test_approval_is_inherited_by_subcategories(demo):
    accessories = Category.objects.get(code="mde-accessories")
    assert not accessories.needs_approval()
    Category.objects.filter(code="mde").update(requires_approval=True)
    accessories.refresh_from_db()
    assert accessories.needs_approval()


def test_current_user_knows_whether_they_approve(approver_client, employee_client):
    assert approver_client.get("/api/auth/me").json()["is_approver"] is True
    assert employee_client.get("/api/auth/me").json()["is_approver"] is False


def test_pending_requests_are_open(approval_setup, employee_client, it_client):
    reservation = request(employee_client, "laptops")
    response = it_client.get("/api/reservations", {"open": True})
    assert reservation["id"] in [r["id"] for r in response.json()["items"]]
    assert Reservation.objects.get(pk=reservation["id"]).completed_at is None


def test_asking_again_shows_the_approver_why_it_was_declined(
    approval_setup, employee_client, approver_client, it_client
):
    declined = request(employee_client, "laptops")
    approver_client.post(
        f"/api/approvals/{declined['id']}/decline", {"comment": "Not this quarter"}, content_type=JSON
    )

    start = date.today() + timedelta(days=3)
    response = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=2)).isoformat(),
            "items": [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}],
            "follows": declined["id"],
        },
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    again = response.json()
    assert again["status"] == "pending_approval"

    seen = approver_client.get(f"/api/reservations/{again['id']}").json()
    assert seen["follows"]["number"] == declined["number"]
    assert seen["follows"]["approval"] == "rejected"
    assert seen["follows"]["approval_comment"] == "Not this quarter"
    assert seen["events"][0]["data"]["follows"] == declined["number"]


def test_follows_only_an_own_request(approval_setup, employee_client, it_client):
    someone_else = request(it_client, "headsets")
    start = date.today() + timedelta(days=3)
    response = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "permanent",
            "start_date": start.isoformat(),
            "items": [{"category": str(Category.objects.get(code="headsets").pk), "quantity": 1}],
            "follows": someone_else["id"],
        },
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    assert response.json()["follows"] is None


def test_menu_counts_show_open_requests_approvals_and_reports(
    approval_setup, employee_client, approver_client
):
    from apps.inventory.models import Asset, AssetIssue
    from apps.inventory.services.issues import update_issue

    def counts(client) -> dict:
        return client.get("/api/portal/menu-counts").json()

    before = counts(employee_client)
    request(employee_client, "laptops")
    assert counts(employee_client) == {**before, "requests": before["requests"] + 1}
    assert counts(approver_client)["approvals"] == 1

    employee = User.objects.get(username="employee")
    issue = AssetIssue.objects.create(asset=Asset.objects.first(), description="Broken", reported_by=employee)
    assert counts(employee_client)["issues"] == before["issues"] + 1
    assert counts(employee_client)["issues_updated"] is before["issues_updated"]

    # IT takes it into work: news for the employee until they look at their reports.
    update_issue(issue, User.objects.get(username="it"), AssetIssue.Status.IN_PROGRESS, by_it=True)
    assert counts(employee_client)["issues_updated"] is True
    assert employee_client.get("/api/portal/my-issues").json()[0]["unseen_update"] is True
    # Opening the report marks it seen.
    assert employee_client.get(f"/api/portal/my-issues/{issue.pk}").status_code == 200
    assert counts(employee_client)["issues_updated"] is False

    # Resolved: no longer counted as open, but still news.
    update_issue(issue, User.objects.get(username="it"), AssetIssue.Status.RESOLVED, "New cable", by_it=True)
    after = counts(employee_client)
    assert after["issues"] == before["issues"] and after["issues_updated"] is True

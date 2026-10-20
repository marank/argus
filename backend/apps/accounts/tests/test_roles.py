from datetime import date, timedelta

import pytest
from django.test import Client

from apps.accounts.models import Role, User
from apps.accounts.permissions import RESOURCE_KEYS, can, effective_permissions
from apps.masterdata.models import Category, Manufacturer

JSON = "application/json"


@pytest.fixture
def staff(demo) -> User:
    """An IT staff member without any role yet."""
    user = User.objects.create_user("staff", password="argus-demo", is_staff=True)
    return user


@pytest.fixture
def staff_client(staff) -> Client:
    client = Client()
    client.login(username="staff", password="argus-demo")
    return client


def grant(user: User, name: str = "Test role", **permissions: str) -> Role:
    role = Role.objects.create(name=name, permissions=permissions)
    role.members.add(user)
    return role


def test_staff_without_role_get_no_it_area(staff_client):
    assert staff_client.get("/api/inventory/assets").status_code == 403
    assert staff_client.get("/api/procurement/orders").status_code == 403
    assert staff_client.get("/api/calendar", {"start": "2026-01-01", "end": "2026-02-01"}).status_code == 403
    # Requests: only their own, like any employee.
    assert staff_client.get("/api/reservations").json()["items"] == []
    # Lookups for forms stay possible, changes do not.
    assert staff_client.get("/api/masterdata/manufacturers").status_code == 200
    response = staff_client.post("/api/masterdata/manufacturers", {"name": "ACME"}, content_type=JSON)
    assert response.status_code == 403
    assert staff_client.get("/api/auth/me").json()["permissions"] == {}


def test_read_right_allows_reading_only(staff, staff_client):
    grant(staff, assets="read", manufacturers="read")
    assert staff_client.get("/api/inventory/assets").status_code == 200
    response = staff_client.post("/api/inventory/assets", {}, content_type=JSON)
    assert response.status_code == 403
    response = staff_client.post("/api/masterdata/manufacturers", {"name": "ACME"}, content_type=JSON)
    assert response.status_code == 403


def test_write_right_allows_changes(staff, staff_client):
    grant(staff, manufacturers="write")
    response = staff_client.post("/api/masterdata/manufacturers", {"name": "ACME"}, content_type=JSON)
    assert response.status_code == 201, response.content
    acme = Manufacturer.objects.get(name="ACME")
    response = staff_client.delete(f"/api/masterdata/manufacturers/{acme.pk}")
    assert response.status_code == 204
    # Other master data stays closed.
    category = Category.objects.first()
    response = staff_client.delete(f"/api/masterdata/categories/{category.pk}")
    assert response.status_code == 403


def test_rights_of_several_roles_add_up(staff):
    grant(staff, "Reader", assets="read", licenses="write")
    grant(staff, "Writer", assets="write")
    assert effective_permissions(staff) == {"assets": "write", "licenses": "write"}


def test_unknown_areas_and_levels_are_dropped(staff):
    role = grant(staff, assets="admin", nonsense="write", issues="read")
    role.refresh_from_db()
    assert role.permissions == {"issues": "read"}


def test_superusers_and_employees(demo):
    admin = User.objects.get(username="admin")
    assert effective_permissions(admin) == dict.fromkeys(RESOURCE_KEYS, "write")
    # Roles do nothing for people outside IT.
    employee = User.objects.get(username="employee")
    grant(employee, assets="write")
    assert not can(employee, "assets")


def test_reservation_rights(staff, staff_client, employee_client):
    start = date.today() + timedelta(days=3)
    reservation = employee_client.post(
        "/api/reservations",
        {
            "title": "Workshop",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=1)).isoformat(),
            "items": [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}],
        },
        content_type=JSON,
    ).json()
    url = f"/api/reservations/{reservation['id']}"

    assert staff_client.get(url).status_code == 404
    grant(staff, reservations="read")
    staff_client.get("/api/auth/me")  # a new request, so the rights are read again
    assert staff_client.get(url).status_code == 200
    assert staff_client.post(f"{url}/confirm", {"items": []}, content_type=JSON).status_code == 403

    Role.objects.filter(members=staff).update(permissions={"reservations": "write"})
    assert staff_client.post(f"{url}/confirm", {"items": []}, content_type=JSON).status_code == 200


def test_only_administrators_manage_roles(staff, staff_client, it_client):
    grant(staff, users="write")
    # Not even with the right to edit users: that would let them raise their own rights.
    assert staff_client.get("/api/accounts/roles").status_code == 403
    response = staff_client.post("/api/accounts/roles", {"name": "Mine"}, content_type=JSON)
    assert response.status_code == 403

    admin = Client()
    admin.login(username="admin", password="argus-demo")
    response = admin.post(
        "/api/accounts/roles",
        {"name": "Purchasing", "permissions": {"procurement": "write"}, "members": [str(staff.pk)]},
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    assert response.json()["members"][0]["username"] == "staff"
    resources = admin.get("/api/accounts/roles/resources").json()
    assert {r["key"] for r in resources} == RESOURCE_KEYS
    assert staff_client.get("/api/auth/me").json()["permissions"] == {
        "users": "write",
        "procurement": "write",
    }


def test_dashboard_shows_only_readable_areas(staff, staff_client, it_client):
    full = it_client.get("/api/dashboard/it").json()
    assert full["asset_status"] and full["recent_events"]

    overview = staff_client.get("/api/dashboard/it").json()
    assert overview["asset_status"] == {} and overview["recent_events"] == []
    assert overview["reservations_submitted"] == 0
    assert staff_client.get("/api/dashboard/widgets/open-orders").status_code == 403
    assert staff_client.get("/api/dashboard/widgets/expiring").json() == []

    grant(staff, assets="read")
    overview = staff_client.get("/api/dashboard/it").json()
    assert overview["asset_status"] == full["asset_status"]

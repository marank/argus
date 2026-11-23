from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.accounts.permissions import PermissionLevel, ResourceKey, can, effective_permissions
from apps.masterdata.models import Category, Manufacturer
from apps.requests.models import AssetRequest

JSON = "application/json"


@pytest.fixture
def staff(demo) -> User:
    """An IT staff member without any role yet."""
    return User.objects.create_user("staff", password="argus-demo", is_staff=True)


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
    assert staff_client.get("/api/requests").json()["items"] == []
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
    assert category is not None
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
    assert effective_permissions(admin) == dict.fromkeys(ResourceKey, PermissionLevel.WRITE)
    # Roles do nothing for people outside IT.
    employee = User.objects.get(username="employee")
    grant(employee, assets="write")
    assert not can(employee, ResourceKey.ASSETS)


def test_asset_request_rights(staff, staff_client, employee_client):
    start = timezone.localdate() + timedelta(days=3)
    asset_request = employee_client.post(
        "/api/requests",
        {
            "title": "Workshop",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=1)).isoformat(),
            "items": [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}],
        },
        content_type=JSON,
    ).json()
    url = f"/api/requests/{asset_request['id']}"

    assert staff_client.get(url).status_code == 404
    grant(staff, requests="read")
    staff_client.get("/api/auth/me")  # a new request, so the rights are read again
    assert staff_client.get(url).status_code == 200
    assert staff_client.post(f"{url}/confirm", {"items": []}, content_type=JSON).status_code == 403

    Role.objects.filter(members=staff).update(permissions={"requests": "write"})
    assert staff_client.post(f"{url}/confirm", {"items": []}, content_type=JSON).status_code == 200


def test_only_administrators_manage_roles(staff, staff_client, it_client, admin_client):
    grant(staff, users="write")
    # Not even with the right to edit users: that would let them raise their own rights.
    assert staff_client.get("/api/accounts/roles").status_code == 403
    response = staff_client.post("/api/accounts/roles", {"name": "Mine"}, content_type=JSON)
    assert response.status_code == 403

    response = admin_client.post(
        "/api/accounts/roles",
        {"name": "Purchasing", "permissions": {"procurement": "write"}, "members": [str(staff.pk)]},
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    assert response.json()["members"][0]["username"] == "staff"
    resources = admin_client.get("/api/accounts/roles/resources").json()
    assert {r["key"] for r in resources} == set(ResourceKey)
    assert staff_client.get("/api/auth/me").json()["permissions"] == {
        "users": "write",
        "procurement": "write",
    }


def test_dashboard_shows_only_readable_areas(staff, staff_client, it_client):
    full = it_client.get("/api/dashboard/it").json()
    assert full["asset_status"]
    assert full["recent_events"]

    overview = staff_client.get("/api/dashboard/it").json()
    assert overview["asset_status"] == {}
    assert overview["recent_events"] == []
    assert overview["requests_submitted"] == 0
    assert staff_client.get("/api/dashboard/widgets/open-orders").status_code == 403
    assert staff_client.get("/api/dashboard/widgets/expiring").json() == []

    grant(staff, assets="read")
    overview = staff_client.get("/api/dashboard/it").json()
    assert overview["asset_status"] == full["asset_status"]


def test_only_administrators_change_or_delete_administrators(staff, staff_client, admin_client):
    grant(staff, users="write")
    admin = User.objects.get(username="admin")
    payload = {"username": "admin", "first_name": "Ada", "last_name": "Admin", "is_active": False}
    response = staff_client.put(f"/api/accounts/users/{admin.pk}", payload, content_type=JSON)
    assert response.status_code == 403
    assert staff_client.delete(f"/api/accounts/users/{admin.pk}").status_code == 403
    admin.refresh_from_db()
    assert admin.is_active

    # Other employees stay editable, and administrators can still edit administrators.
    employee = User.objects.get(username="employee")
    payload = {"username": "employee", "first_name": "Erika", "last_name": "Neu"}
    response = staff_client.put(f"/api/accounts/users/{employee.pk}", payload, content_type=JSON)
    assert response.status_code == 200, response.content
    payload = {"username": "admin", "first_name": "Ada", "last_name": "Lovelace"}
    response = admin_client.put(f"/api/accounts/users/{admin.pk}", payload, content_type=JSON)
    assert response.status_code == 200, response.content


def test_nobody_deletes_their_own_account(admin_client):
    admin = User.objects.get(username="admin")
    assert admin_client.delete(f"/api/accounts/users/{admin.pk}").status_code == 409


def test_employees_cannot_read_master_data(employee_client):
    for path in (
        "accounts/users",
        "accounts/departments",
        "masterdata/suppliers",
        "masterdata/locations",
        "masterdata/number-sequences",
    ):
        assert employee_client.get(f"/api/{path}").status_code == 403, path
    admin = User.objects.get(username="admin")
    assert employee_client.get(f"/api/accounts/users/{admin.pk}").status_code == 403


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/inventory/assets"),
        ("get", "/api/inventory/issues"),
        ("get", "/api/terminal/pickups"),
        ("get", "/api/portal/availability?start=2026-01-01"),
        ("get", "/api/calendar?start=2026-01-01&end=2026-01-31"),
        ("get", "/api/dashboard/widgets/team-load"),
        ("post", "/api/requests/quick"),
        ("post", "/api/requests/direct"),
        # Not even for their own request.
        ("post", "/api/requests/{own}/extend"),
        ("post", "/api/requests/{own}/remind"),
    ],
)
def test_employees_stay_out_of_it_work(employee_client, method, path):
    own = AssetRequest.objects.filter(requester__username="employee").order_by("pk").first()
    assert own is not None
    response = getattr(employee_client, method)(path.format(own=own.pk), content_type=JSON)
    assert response.status_code == 403


def test_only_administrators_appoint_administrators(staff, staff_client, admin_client):
    grant(staff, users="write")
    url = f"/api/accounts/users/{staff.pk}"
    data = {"username": "staff", "is_staff": True}

    # The right to edit users is not enough, not even for oneself.
    response = staff_client.put(url, {**data, "is_superuser": True}, content_type=JSON)
    assert response.status_code == 403
    response = staff_client.post(
        "/api/accounts/users", {"username": "boss", "is_superuser": True}, content_type=JSON
    )
    assert response.status_code == 403
    # Sending the unchanged status, or none at all, is fine.
    assert staff_client.put(url, {**data, "is_superuser": False}, content_type=JSON).status_code == 200
    assert staff_client.put(url, {**data, "job_title": "Support"}, content_type=JSON).status_code == 200

    response = admin_client.put(url, {**data, "is_superuser": True}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert response.json()["is_superuser"] is True
    staff.refresh_from_db()
    assert staff.is_superuser

    # Leaving the field out keeps the status.
    assert admin_client.put(url, data, content_type=JSON).status_code == 200
    staff.refresh_from_db()
    assert staff.is_superuser

    # Administrators demote others, but never themselves.
    own = User.objects.get(username="admin")
    response = admin_client.put(
        f"/api/accounts/users/{own.pk}",
        {"username": "admin", "is_superuser": False},
        content_type=JSON,
    )
    assert response.status_code == 409
    assert User.objects.get(pk=own.pk).is_superuser
    assert admin_client.put(url, {**data, "is_superuser": False}, content_type=JSON).status_code == 200
    staff.refresh_from_db()
    assert not staff.is_superuser


def test_nobody_deactivates_themselves(admin_client):
    own = User.objects.get(username="admin")
    url = f"/api/accounts/users/{own.pk}"
    data = {"username": "admin", "is_staff": True}
    assert admin_client.put(url, {**data, "is_active": False}, content_type=JSON).status_code == 409
    assert User.objects.get(pk=own.pk).is_active

    # Another administrator may deactivate them, e.g. the one from ADMIN_USERNAME.
    User.objects.create_superuser("other", password="argus-demo")
    other = Client()
    other.login(username="other", password="argus-demo")
    assert other.put(url, {**data, "is_active": False}, content_type=JSON).status_code == 200
    assert not User.objects.get(pk=own.pk).is_active


def test_roles_and_teams_in_the_user_form(staff, staff_client, admin_client):
    from apps.accounts.models import Team

    grant(staff, users="write")
    role = Role.objects.create(name="Support", permissions={"inventory": "read"})
    team = Team.objects.create(name="Ledgerline")
    colleague = User.objects.create_user("colleague", is_staff=True)
    url = f"/api/accounts/users/{colleague.pk}"
    data = {"username": "colleague", "is_staff": True}

    # Roles only from administrators, teams only with the right to edit teams.
    assert staff_client.put(url, {**data, "roles": [str(role.pk)]}, content_type=JSON).status_code == 403
    assert staff_client.put(url, {**data, "teams": [str(team.pk)]}, content_type=JSON).status_code == 403
    grant(staff, "Teams", teams="write")
    response = staff_client.put(url, {**data, "teams": [str(team.pk)], "roles": []}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert [t["name"] for t in response.json()["teams"]] == ["Ledgerline"]

    response = admin_client.put(url, {**data, "roles": [str(role.pk)]}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert [r["name"] for r in response.json()["roles"]] == ["Support"]
    # Leaving both out keeps them.
    assert staff_client.put(url, data, content_type=JSON).status_code == 200
    assert list(colleague.roles.all()) == [role]
    assert list(colleague.teams.all()) == [team]


def test_terminal_location_only_for_terminals(admin_client):
    from apps.masterdata.models import Location

    location = Location.objects.first()
    assert location is not None
    user = User.objects.create_user("kiosk")
    url = f"/api/accounts/users/{user.pk}"
    data = {"username": "kiosk", "terminal_location": str(location.pk)}

    terminal = admin_client.put(url, {**data, "is_terminal": True}, content_type=JSON).json()
    assert terminal["terminal_location"]
    employee = admin_client.put(url, {**data, "is_terminal": False}, content_type=JSON).json()
    assert employee["terminal_location"] is None

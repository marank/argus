from django.test import Client

from apps.accounts.models import SignInThrottle, User
from apps.accounts.services import throttle

JSON = "application/json"
PASSWORD = "argus-demo"
NEW = "Neues-Passwort-2026!"


def change(client: Client, current=PASSWORD, new=NEW):
    return client.post(
        "/api/auth/password", {"current_password": current, "new_password": new}, content_type=JSON
    )


def set_for(client: Client, user: User, password=NEW):
    return client.post(f"/api/accounts/users/{user.pk}/password", {"password": password}, content_type=JSON)


def can_log_in(username: str, password: str) -> bool:
    response = Client().post(
        "/api/auth/login", {"username": username, "password": password}, content_type=JSON
    )
    return response.status_code == 200


def test_user_changes_own_password_and_stays_signed_in(employee_client):
    assert change(employee_client).status_code == 204
    assert employee_client.get("/api/auth/me").status_code == 200
    assert can_log_in("employee", NEW)
    assert not can_log_in("employee", PASSWORD)


def test_change_needs_the_current_password(employee_client):
    response = change(employee_client, current="wrong")
    assert response.status_code == 403
    assert can_log_in("employee", PASSWORD)


def test_new_password_must_follow_the_rules(employee_client):
    response = change(employee_client, new="123")
    assert response.status_code == 422
    assert can_log_in("employee", PASSWORD)


def test_change_can_be_switched_off_per_user(employee_client):
    User.objects.filter(username="employee").update(can_change_password=False)
    assert change(employee_client).status_code == 403


def test_directory_accounts_change_it_in_the_directory(employee_client):
    User.objects.filter(username="employee").update(ldap_dn="CN=employee,DC=example,DC=com")
    assert change(employee_client).status_code == 409


def test_other_sessions_end_after_a_change(demo):
    other = Client()
    other.force_login(User.objects.get(username="employee"))
    mine = Client()
    mine.force_login(User.objects.get(username="employee"))
    assert change(mine).status_code == 204
    assert other.get("/api/auth/me").status_code == 401


def test_administrator_sets_password_of_local_account(admin_client):
    terminal = User.objects.get(username="terminal")
    SignInThrottle.objects.create(key=throttle.password_key("terminal"), failures=10)
    response = set_for(admin_client, terminal)
    assert response.status_code == 200
    assert response.json()["has_password"] is True
    assert can_log_in("terminal", NEW)


def test_new_account_has_no_password_until_one_is_set(admin_client):
    created = admin_client.post("/api/accounts/users", {"username": "neu"}, content_type=JSON)
    assert created.status_code == 201, created.content
    assert created.json()["has_password"] is False
    assert created.json()["can_change_password"] is True
    user = User.objects.get(username="neu")
    assert set_for(admin_client, user).status_code == 200
    assert can_log_in("neu", NEW)


def test_only_administrators_set_passwords(it_client):
    employee = User.objects.get(username="employee")
    assert set_for(it_client, employee).status_code == 403


def test_administrator_cannot_set_own_or_directory_password(admin_client):
    me = User.objects.get(username="admin")
    assert set_for(admin_client, me).status_code == 409
    employee = User.objects.get(username="employee")
    User.objects.filter(pk=employee.pk).update(ldap_dn="CN=employee,DC=example,DC=com")
    assert set_for(admin_client, employee).status_code == 409


def test_set_password_follows_the_rules(admin_client):
    employee = User.objects.get(username="employee")
    assert set_for(admin_client, employee, password="123").status_code == 422
    assert can_log_in("employee", PASSWORD)


def test_flag_is_saved_with_the_user(admin_client):
    employee = User.objects.get(username="employee")
    detail = admin_client.get(f"/api/accounts/users/{employee.pk}").json()
    payload = {
        "username": detail["username"],
        "first_name": detail["first_name"],
        "last_name": detail["last_name"],
        "can_change_password": False,
    }
    response = admin_client.put(f"/api/accounts/users/{employee.pk}", payload, content_type=JSON)
    assert response.status_code == 200, response.content
    employee.refresh_from_db()
    assert employee.can_change_password is False

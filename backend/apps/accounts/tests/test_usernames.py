import pytest
from django.db import IntegrityError
from django.test import Client

from apps.accounts.models import User

JSON = "application/json"


def api_login(username: str, password: str):
    return Client().post("/api/auth/login", {"username": username, "password": password}, content_type=JSON)


@pytest.mark.parametrize("spelling", ["admin", "Admin", "ADMIN"])
def test_login_ignores_case(demo, spelling):
    response = api_login(spelling, "argus-demo")
    assert response.status_code == 200, response.content
    # The stored spelling stays as it was created.
    assert response.json()["username"] == "admin"


def test_usernames_differing_only_in_case_are_refused(demo, it_client):
    response = it_client.post(
        "/api/accounts/users", {"username": "Employee", "first_name": "Copy"}, content_type=JSON
    )
    assert response.status_code == 422, response.content
    assert "__all__" in response.json()["errors"]

    with pytest.raises(IntegrityError):
        User.objects.create(username="EMPLOYEE")


def test_created_users_have_no_usable_password(demo, it_client):
    response = it_client.post(
        "/api/accounts/users", {"username": "m.user@example.com", "is_staff": True}, content_type=JSON
    )
    assert response.status_code == 201, response.content
    user = User.objects.get(username="m.user@example.com")
    assert not user.has_usable_password()

from django.test import Client

from apps.accounts.models import User
from apps.core.models import SiteSettings

JSON = "application/json"
PASSWORD = "argus-demo"


def login(username: str) -> Client:
    client = Client()
    response = client.post("/api/auth/login", {"username": username, "password": PASSWORD}, content_type=JSON)
    assert response.status_code == 200, response.content
    return client


def expiry_hours(client: Client) -> float:
    return client.session.get_expiry_age() / 3600


def test_sign_in_lasts_as_long_as_the_site_setting(demo):
    assert expiry_hours(login("employee")) == 12
    settings = SiteSettings.load()
    settings.session_hours = 9
    settings.save()
    assert expiry_hours(login("employee")) == 9


def test_own_value_overrides_the_site_setting(demo):
    User.objects.filter(username="terminal").update(session_hours=72)
    assert expiry_hours(login("terminal")) == 72


def test_administrator_changes_the_duration(admin_client):
    rules = admin_client.get("/api/settings/site").json()["rules"]
    assert rules["session_hours"] == 12
    response = admin_client.put(
        "/api/settings/site", {"rules": {**rules, "session_hours": 10}}, content_type=JSON
    )
    assert response.status_code == 200, response.content
    assert SiteSettings.load().session_hours == 10
    too_long = admin_client.put(
        "/api/settings/site", {"rules": {**rules, "session_hours": 1000}}, content_type=JSON
    )
    assert too_long.status_code == 422


def test_duration_is_saved_with_the_user(admin_client):
    terminal = User.objects.get(username="terminal")
    detail = admin_client.get(f"/api/accounts/users/{terminal.pk}").json()
    assert detail["session_hours"] is None
    payload = {"username": "terminal", "is_terminal": True, "session_hours": 48}
    response = admin_client.put(f"/api/accounts/users/{terminal.pk}", payload, content_type=JSON)
    assert response.status_code == 200, response.content
    terminal.refresh_from_db()
    assert terminal.session_hours == 48

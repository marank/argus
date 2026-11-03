from apps.accounts.models import User

JSON = "application/json"


def test_theme_follows_the_system_until_the_user_picks_one(employee_client):
    assert employee_client.get("/api/auth/me").json()["theme"] == "system"

    response = employee_client.patch("/api/auth/me", {"theme": "solarized"}, content_type=JSON)
    assert response.json()["theme"] == "solarized"
    assert User.objects.get(username="employee").theme == User.Theme.SOLARIZED


def test_unknown_theme_is_rejected(employee_client):
    response = employee_client.patch("/api/auth/me", {"theme": "neon"}, content_type=JSON)
    assert response.status_code == 422

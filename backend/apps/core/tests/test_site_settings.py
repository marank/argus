from django.test import Client

from apps.core.features import effective_flags

JSON = "application/json"


def admin_client() -> Client:
    client = Client()
    client.login(username="admin", password="argus-demo")
    return client


def switch(client: Client, **flags: bool) -> dict:
    response = client.put("/api/settings/site", {"flags": flags}, content_type=JSON)
    assert response.status_code == 200, response.content
    return response.json()


def test_everything_is_on_by_default(employee_client):
    flags = employee_client.get("/api/settings/site").json()["flags"]
    assert all(flags.values())


def test_feature_follows_its_modules():
    flags = effective_flags({"licenses": False})
    assert flags["calendar_license_expiry"] is False
    assert flags["software_requests"] is False
    assert flags["calendar_warranty"] is True


def test_only_administrators_change_settings(it_client):
    response = it_client.put("/api/settings/site", {"flags": {"licenses": False}}, content_type=JSON)
    assert response.status_code == 403


def test_switched_off_module_is_gone_from_the_api(demo, it_client, employee_client):
    admin = admin_client()
    result = switch(admin, licenses=False)
    assert result["flags"]["licenses"] is False
    assert result["stored"]["calendar_license_expiry"] is True  # kept for when licenses come back

    assert it_client.get("/api/inventory/licenses").status_code == 404
    assert employee_client.get("/api/portal/my-licenses").status_code == 404
    # Software is no longer offered in the request catalog.
    catalog = employee_client.get("/api/portal/catalog").json()
    assert all(category["kind"] != "software" for category in catalog)

    switch(admin, licenses=True)
    assert it_client.get("/api/inventory/licenses").status_code == 200


def test_calendar_hides_switched_off_kinds(demo, it_client):
    switch(admin_client(), calendar_license_expiry=False)
    response = it_client.get(
        "/api/calendar", {"start": "2026-01-01", "end": "2026-12-31", "kinds": ["license"]}
    )
    assert all(entry["kind"] != "license" for entry in response.json())

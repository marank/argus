from typing import Any

from django.test import Client

from apps.core.features import FeatureKey, effective_flags
from apps.inventory.models import License

JSON = "application/json"


def switch(client: Client, **flags: bool) -> dict[str, Any]:
    response = client.put("/api/settings/site", {"flags": flags}, content_type=JSON)
    assert response.status_code == 200, response.content
    result: dict[str, Any] = response.json()
    return result


def test_everything_is_on_by_default(employee_client):
    flags = employee_client.get("/api/settings/site").json()["flags"]
    assert all(flags.values())


def test_feature_follows_its_modules():
    flags = effective_flags({"licenses": False})
    assert flags[FeatureKey.CALENDAR_LICENSE_EXPIRY] is False
    assert flags[FeatureKey.SOFTWARE_REQUESTS] is False
    assert flags[FeatureKey.CALENDAR_WARRANTY] is True


def test_only_administrators_change_settings(it_client):
    response = it_client.put("/api/settings/site", {"flags": {"licenses": False}}, content_type=JSON)
    assert response.status_code == 403


def test_switched_off_module_is_gone_from_the_api(it_client, employee_client, admin_client):
    admin = admin_client
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


def test_calendar_hides_switched_off_kinds(it_client, admin_client):
    license = License.objects.exclude(valid_until=None).order_by("valid_until").first()
    assert license is not None and license.valid_until is not None
    day = license.valid_until.isoformat()

    def kinds() -> set[str]:
        response = it_client.get("/api/calendar", {"start": day, "end": day, "kinds": ["license"]})
        return {entry["kind"] for entry in response.json()}

    assert kinds() == {"license"}
    switch(admin_client, calendar_license_expiry=False)
    assert kinds() == set()

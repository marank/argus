import pytest
from django.core.exceptions import ValidationError
from django.test import Client

from apps.accounts.models import User
from apps.core.models import NumberSequence
from apps.core.services.numbering import next_number

JSON = "application/json"


def test_sequence_formats_and_increments(db):
    sequence = NumberSequence.objects.create(
        code="test",
        name="Test",
        prefix="LT-",
        pattern="{prefix}{year}-{seq}",
        padding=3,
        reset_period=NumberSequence.ResetPeriod.YEARLY,
    )
    first, second = next_number(sequence), next_number(sequence)
    assert first.startswith("LT-") and first.endswith("-001")
    assert second.endswith("-002")


def test_api_requires_login(client, db):
    assert client.get("/api/inventory/assets").status_code == 401


def test_employee_cannot_access_inventory(employee_client):
    assert employee_client.get("/api/inventory/assets").status_code == 403


def test_ids_are_uuids(it_client):
    import uuid

    asset = it_client.get("/api/inventory/assets").json()["items"][0]
    assert uuid.UUID(asset["id"])
    assert it_client.get(f"/api/inventory/assets/{asset['id']}").status_code == 200
    assert it_client.get("/api/inventory/assets/1").status_code == 404


def test_all_master_data_lists_load(it_client):
    for path in (
        "accounts/users",
        "accounts/departments",
        "masterdata/manufacturers",
        "masterdata/suppliers",
        "masterdata/categories",
        "masterdata/locations",
        "masterdata/models",
        "masterdata/number-sequences",
    ):
        response = it_client.get(f"/api/{path}")
        assert response.status_code == 200, (path, response.content)
        assert response.json()["count"] > 0, path


def test_health_endpoint_is_public(client, db):
    assert client.get("/api/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    "pattern",
    ["{prefix.__class__}{seq}", "{seq:>999999999}{seq}", "{seq!r}{seq}", "{0}{seq}", "{seq}{", "{nope}{seq}"],
)
def test_pattern_allows_only_plain_placeholders(db, pattern):
    sequence = NumberSequence(code="x", name="X", pattern=pattern)
    with pytest.raises(ValidationError):
        sequence.full_clean()
    with pytest.raises(ValueError):
        sequence.format(1)


def test_preview_needs_the_right_to_edit_number_sequences(it_client):
    payload = {"code": "x", "name": "X", "prefix": "LT-", "pattern": "{prefix}{seq}", "padding": 3}
    response = it_client.post("/api/masterdata/number-sequences/preview", payload, content_type=JSON)
    assert response.status_code == 200, response.content
    assert response.json()["examples"][0] == "LT-001"

    User.objects.create_user("staff", password="argus-demo", is_staff=True)
    staff = Client()
    staff.login(username="staff", password="argus-demo")
    response = staff.post("/api/masterdata/number-sequences/preview", payload, content_type=JSON)
    assert response.status_code == 403

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


def test_sequence_code_is_optional_but_unique_and_fixed_for_system_sequences(demo):
    admin = Client()
    admin.login(username="admin", password="argus-demo")
    url = "/api/masterdata/number-sequences"
    for name in ("Headsets", "Docks"):
        response = admin.post(url, {"name": name}, content_type=JSON)
        assert response.status_code == 201, response.content

    response = admin.post(url, {"name": "Copy", "code": "asset"}, content_type=JSON)
    assert response.status_code == 422, response.content
    assert "code" in response.json()["errors"]

    # Argus draws inventory numbers by the code "asset"; renaming it would start a new range.
    asset = NumberSequence.objects.get(code="asset")
    response = admin.put(
        f"{url}/{asset.pk}", {"name": asset.name, "code": "", "pattern": asset.pattern}, content_type=JSON
    )
    assert response.status_code == 422, response.content
    assert "code" in response.json()["errors"]


def test_system_sequences_exist_from_the_start(db):
    # Created by a migration, so they can be set up before the first number is drawn.
    system = NumberSequence.objects.filter(is_system=True)
    assert set(system.values_list("code", flat=True)) == {"asset", "request", "purchase-order"}


def test_system_sequences_cannot_be_deleted(demo):
    admin = Client()
    admin.login(username="admin", password="argus-demo")
    url = "/api/masterdata/number-sequences"
    asset = NumberSequence.objects.get(code="asset")
    assert admin.delete(f"{url}/{asset.pk}").status_code == 409
    own = NumberSequence.objects.create(name="Headsets")
    assert admin.delete(f"{url}/{own.pk}").status_code == 204


def test_numbers_already_taken_are_skipped(db):
    sequence = NumberSequence.objects.create(name="Test", prefix="N", padding=3)
    taken = {"N001", "N002"}
    assert next_number(sequence, taken=taken.__contains__) == "N003"
    # Changing the format afterwards (N001 -> N0001) starts no clash: the strings differ.
    sequence.refresh_from_db()
    sequence.padding = 4
    sequence.save()
    assert next_number(sequence, taken=taken.__contains__) == "N0004"


def test_a_hand_entered_inventory_number_is_skipped_by_the_sequence(it_client):
    # Used to fail with HTTP 500 when the sequence reached the number entered by hand.
    from apps.inventory.models import Asset
    from apps.masterdata.models import AssetModel

    model = AssetModel.objects.filter(tracking="serialized").first()
    sequence = model.category.effective_number_sequence() or NumberSequence.objects.get(code="asset")
    sequence.refresh_from_db()
    upcoming = sequence.preview()
    url = "/api/inventory/assets"
    response = it_client.post(url, {"model": str(model.pk), "inventory_number": upcoming}, content_type=JSON)
    assert response.status_code == 201, response.content
    response = it_client.post(url, {"model": str(model.pk)}, content_type=JSON)
    assert response.status_code == 201, response.content
    assert response.json()["inventory_number"] != upcoming
    assert Asset.objects.filter(inventory_number=upcoming).count() == 1


def test_migration_renames_the_request_sequence_and_moves_hyphens(db):
    from importlib import import_module

    from django.apps import apps

    migration = import_module("apps.core.migrations.0005_request_sequence_hyphen_in_pattern")
    # The state before: the system sequences as 0004 created them, one of them changed by hand.
    NumberSequence.objects.filter(code="request").update(
        code="reservation", name="Reservations", prefix="RES-", pattern="{prefix}{year}-{seq}"
    )
    NumberSequence.objects.filter(code="asset").update(prefix="INV-", pattern="{prefix}{seq}")
    NumberSequence.objects.filter(code="purchase-order").update(prefix="B-", pattern="{prefix}{yy}/{seq}")
    before = {s.code: s.format(7) for s in NumberSequence.objects.all()}

    migration.forward(apps, None)

    request = NumberSequence.objects.get(code="request")
    assert (request.name, request.prefix, request.pattern) == ("Requests", "RES", "{prefix}-{year}-{seq}")
    asset = NumberSequence.objects.get(code="asset")
    assert (asset.prefix, asset.pattern) == ("INV", "{prefix}-{seq}")
    order = NumberSequence.objects.get(code="purchase-order")
    assert (order.prefix, order.pattern) == ("B-", "{prefix}{yy}/{seq}")
    # The numbers themselves stay the same.
    after = {s.code: s.format(7) for s in NumberSequence.objects.all()}
    assert after == {"request" if code == "reservation" else code: v for code, v in before.items()}

    migration.backward(apps, None)
    reservation = NumberSequence.objects.get(code="reservation")
    assert (reservation.name, reservation.prefix) == ("Reservations", "RES-")

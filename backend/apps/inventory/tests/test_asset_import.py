from decimal import Decimal

import pytest

from apps.inventory.models import Asset, AssetEvent, AssetEventKind
from apps.inventory.services.asset_import import _parse_date, _parse_decimal, clean_cell
from apps.masterdata.models import AssetModel, Location

JSON = "application/json"
PREVIEW = "/api/inventory/assets/import/preview"
IMPORT = "/api/inventory/assets/import"

# Two rows of an MDM export (Fleetwise MDM): "'--" for empty cells, MACs in lower case.
ROWS = [
    {"name": "H102", "model": "SX58", "mac_address": "00:00:5e:00:53:01", "serial_number": "31415A926B"},
    {
        "name": "H064",
        "model": "SX58",
        "mac_address": "00:00:5e:00:53:02",
        "serial_number": "27182B8281",
        "imei": "'--",
    },
]


def test_preview_saves_nothing_and_import_creates(it_client):
    before = Asset.objects.count()
    warehouse = Location.objects.get(code="WH")
    payload = {"rows": ROWS, "defaults": {"location": str(warehouse.pk), "condition": "good"}}

    preview = it_client.post(PREVIEW, payload, content_type=JSON)
    assert preview.status_code == 200, preview.content
    body = preview.json()
    assert (body["created"], body["failed"]) == (2, 0)
    numbers = [row["inventory_number"] for row in body["rows"]]
    assert all(n.startswith("MDE-") for n in numbers)
    assert all(row["asset_id"] is None for row in body["rows"])
    assert {"field": "mac_address", "old": "", "new": "00:00:5E:00:53:01"} in body["rows"][0]["changes"]
    assert Asset.objects.count() == before

    done = it_client.post(IMPORT, payload, content_type=JSON).json()
    assert done["created"] == 2
    # The preview promised the same numbers.
    assert [row["inventory_number"] for row in done["rows"]] == numbers
    asset = Asset.objects.get(serial_number="31415A926B")
    assert (asset.name, asset.mac_address, asset.location, asset.condition, asset.imei) == (
        "H102",
        "00:00:5E:00:53:01",
        warehouse,
        "good",
        "",
    )
    assert AssetEvent.objects.filter(asset=asset, kind=AssetEventKind.CREATED).exists()

    # The same file again matches by serial number: nothing changes.
    again = it_client.post(IMPORT, payload, content_type=JSON).json()
    assert (again["created"], again["unchanged"]) == (0, 2)


def test_update_existing_and_skip(it_client):
    asset = Asset.objects.filter(model__name="SX58").exclude(serial_number="").first()
    assert asset is not None
    row = {"serial_number": asset.serial_number, "name": "NEW-HOST", "status": "Defekt"}
    response = it_client.post(PREVIEW, {"rows": [row]}, content_type=JSON).json()
    # "Defekt" is a condition, not a status.
    assert response["failed"] == 1 and "Defekt" in response["rows"][0]["errors"][0]

    row["status"] = "In Reparatur"
    response = it_client.post(IMPORT, {"rows": [row]}, content_type=JSON).json()
    assert response["updated"] == 1
    changes = {c["field"]: c for c in response["rows"][0]["changes"]}
    assert changes["name"]["new"] == "NEW-HOST"
    asset.refresh_from_db()
    assert (asset.name, asset.status) == ("NEW-HOST", "in_repair")

    row["name"] = "OTHER"
    skipped = it_client.post(IMPORT, {"rows": [row], "existing": "skip"}, content_type=JSON).json()
    assert skipped["skipped"] == 1
    asset.refresh_from_db()
    assert asset.name == "NEW-HOST"


def test_row_errors_leave_other_rows(it_client):
    sx58 = AssetModel.objects.get(name="SX58")
    rows = [
        {"serial_number": "OK-1"},
        {"serial_number": "BAD-1", "model": "Nokia 3310"},
        {"serial_number": "BAD-2", "purchase_date": "someday"},
        {"serial_number": "BAD-3", "mac_address": "xyz"},
    ]
    response = it_client.post(IMPORT, {"rows": rows, "defaults": {"model": str(sx58.pk)}}, content_type=JSON)
    body = response.json()
    assert (body["created"], body["failed"]) == (1, 3), body
    assert Asset.objects.filter(serial_number="OK-1").exists()
    assert not Asset.objects.filter(serial_number__startswith="BAD-").exists()
    assert "MAC" in body["rows"][3]["errors"][0]


def test_without_model_and_without_matching(it_client):
    body = it_client.post(PREVIEW, {"rows": [{"serial_number": "X"}]}, content_type=JSON).json()
    assert "model" in body["rows"][0]["errors"][0].lower()

    asset = Asset.objects.exclude(serial_number="").first()
    assert asset is not None
    rows = [{"serial_number": asset.serial_number, "model": asset.model.full_name}]
    body = it_client.post(PREVIEW, {"rows": rows, "match_by": None}, content_type=JSON).json()
    # Without matching the row is new, and the serial number is taken for this model.
    assert body["failed"] == 1


def test_employee_cannot_import(employee_client):
    assert employee_client.post(PREVIEW, {"rows": ROWS}, content_type=JSON).status_code == 403


@pytest.mark.parametrize(
    ("text", "expected"),
    [("'--", ""), ("  -- ", ""), ("'0815", "0815"), ("H102", "H102")],
)
def test_clean_cell(text, expected):
    assert clean_cell(text) == expected


def test_parsers():
    assert str(_parse_date("31.03.2026")) == "2026-03-31"
    assert str(_parse_date("2026-03-31T10:00")) == "2026-03-31"
    assert _parse_decimal("1.234,56 €") == Decimal("1234.56")
    assert _parse_decimal("1,234.56") == Decimal("1234.56")
    assert _parse_decimal("2,10") == Decimal("2.10")


def test_ignore_case_when_matching(it_client):
    asset = Asset.objects.filter(model__name="SX58").exclude(serial_number="").first()
    assert asset is not None
    rows = [{"serial_number": asset.serial_number.lower(), "name": "LOWER"}]
    payload = {"rows": rows, "defaults": {"model": str(asset.model_id)}}

    exact = it_client.post(PREVIEW, payload, content_type=JSON).json()
    assert exact["rows"][0]["action"] == "create"

    any_case = it_client.post(PREVIEW, {**payload, "ignore_case": True}, content_type=JSON).json()
    assert any_case["rows"][0]["action"] == "update"
    assert any_case["rows"][0]["inventory_number"] == asset.inventory_number

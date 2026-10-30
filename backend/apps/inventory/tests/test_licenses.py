import uuid
from datetime import date, timedelta
from typing import Any

from apps.accounts.models import User
from apps.inventory.models import Asset, License
from apps.masterdata.models import AssetModel, Category

JSON = "application/json"


def license_payload(model: AssetModel, **changes) -> dict[str, Any]:
    return {"model": str(model.pk), "seats": 2, "assign_to": "user", **changes}


def test_license_list_counts_used_seats(it_client):
    response = it_client.get("/api/inventory/licenses?ordering=model__name")
    assert response.status_code == 200, response.content
    by_name = {item["model"]["name"]: item for item in response.json()["items"]}
    assert by_name["365 Business Standard"]["seats"] == 25
    assert by_name["365 Business Standard"]["seats_used"] == 4
    assert by_name["AutoCAD LT"]["assign_to"] == "device"
    assert by_name["AutoCAD LT"]["category"]["kind"] == "software"


def test_assign_seats_until_full(it_client):
    acrobat = AssetModel.objects.get(name="Acrobat Pro")
    response = it_client.post("/api/inventory/licenses", license_payload(acrobat), content_type=JSON)
    assert response.status_code == 201, response.content
    license_id = response.json()["id"]
    users = list(User.objects.filter(username__in=["employee", "sales", "admin"]).order_by("username"))

    for user in users[:2]:
        response = it_client.post(
            f"/api/inventory/licenses/{license_id}/assignments", {"user": str(user.pk)}, content_type=JSON
        )
        assert response.status_code == 201, response.content
    assert response.json()["seats_used"] == 2
    assert len(response.json()["assignments"]) == 2

    # No seat left.
    response = it_client.post(
        f"/api/inventory/licenses/{license_id}/assignments", {"user": str(users[2].pk)}, content_type=JSON
    )
    assert response.status_code == 409

    # Seats cannot drop below what is assigned.
    response = it_client.put(
        f"/api/inventory/licenses/{license_id}", license_payload(acrobat, seats=1), content_type=JSON
    )
    assert response.status_code == 409

    # Freeing a seat makes room again.
    assignment = License.objects.get(pk=license_id).assignments.first()
    assert assignment is not None
    response = it_client.delete(f"/api/inventory/licenses/{license_id}/assignments/{assignment.pk}")
    assert response.json()["seats_used"] == 1


def test_assignment_must_match_license_type(it_client):
    autocad = License.objects.get(model__name="AutoCAD LT")
    employee = User.objects.get(username="employee")
    response = it_client.post(
        f"/api/inventory/licenses/{autocad.pk}/assignments", {"user": str(employee.pk)}, content_type=JSON
    )
    assert response.status_code == 409

    laptop = Asset.objects.filter(model__name="ThinkPad T14 Gen 5").first()
    assert laptop is not None
    response = it_client.post(
        f"/api/inventory/licenses/{autocad.pk}/assignments", {"asset": str(laptop.pk)}, content_type=JSON
    )
    assert response.status_code == 201, response.content
    detail = it_client.get(f"/api/inventory/assets/{laptop.pk}").json()
    assert [entry["model"]["name"] for entry in detail["licenses"]] == ["AutoCAD LT"]


def test_expired_license_cannot_be_assigned(it_client):
    License.objects.filter(model__name="Acrobat Pro").update(valid_until=date.today() - timedelta(days=1))
    acrobat = License.objects.get(model__name="Acrobat Pro")
    admin = User.objects.get(username="admin")
    response = it_client.post(
        f"/api/inventory/licenses/{acrobat.pk}/assignments", {"user": str(admin.pk)}, content_type=JSON
    )
    assert response.status_code == 409


def test_license_needs_software_model(it_client):
    laptop = AssetModel.objects.get(name="ThinkPad T14 Gen 5")
    response = it_client.post("/api/inventory/licenses", license_payload(laptop), content_type=JSON)
    assert response.status_code == 422


def test_category_and_model_types_must_match(it_client):
    office = Category.objects.get(code="office-software")
    response = it_client.post(
        "/api/masterdata/categories",
        {"name": "Notebooks", "code": "notebooks", "parent": str(office.pk), "kind": "hardware"},
        content_type=JSON,
    )
    assert response.status_code == 422

    manufacturer = AssetModel.objects.get(name="Acrobat Pro").manufacturer
    response = it_client.post(
        "/api/masterdata/models",
        {
            "name": "Reader",
            "manufacturer": str(manufacturer.pk),
            "category": str(office.pk),
            "tracking": "serialized",
        },
        content_type=JSON,
    )
    assert response.status_code == 422


def test_software_is_not_a_device(it_client):
    acrobat = AssetModel.objects.get(name="Acrobat Pro")
    response = it_client.post("/api/inventory/assets", {"model": str(acrobat.pk)}, content_type=JSON)
    assert response.status_code == 422


def test_software_request_is_filled_with_a_license_seat(employee_client, it_client):
    from apps.inventory.models import LicenseAssignment

    acrobat = AssetModel.objects.get(name="Acrobat Pro")
    start = date.today() + timedelta(days=1)
    response = employee_client.post(
        "/api/requests",
        {
            "title": "PDF forms",
            "duration": "permanent",
            "start_date": start.isoformat(),
            "items": [{"asset_model": str(acrobat.pk), "quantity": 1}],
        },
        content_type=JSON,
    )
    assert response.status_code == 201, response.content
    asset_request = response.json()
    rid, item = asset_request["id"], asset_request["items"][0]
    assert item["is_software"] is True

    response = it_client.post(
        f"/api/requests/{rid}/confirm",
        {"items": [{"id": item["id"], "quantity_confirmed": 1}]},
        content_type=JSON,
    )
    assert response.json()["items"][0]["quantity_missing"] == 1
    # Without a seat the request cannot be marked ready.
    assert it_client.post(f"/api/requests/{rid}/ready", {}, content_type=JSON).status_code == 409

    candidates = it_client.get(f"/api/requests/items/{item['id']}/candidates").json()
    assert candidates["licenses"] and candidates["licenses"][0]["free_seats"] > 0
    assert it_client.post(f"/api/requests/{rid}/auto-allocate").json()["allocated"] == 1
    employee = User.objects.get(username="employee")
    assert LicenseAssignment.objects.filter(license__model=acrobat, user=employee).exists()

    # Nothing to collect: marking ready hands it out and completes the permanent request.
    response = it_client.post(f"/api/requests/{rid}/ready", {"handover_mode": "pickup"}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert response.json()["status"] == "completed"
    assert response.json()["items"][0]["allocations"][0]["license"]["model"]["name"] == "Acrobat Pro"


def test_temporary_software_seat_is_taken_back(employee_client, it_client):
    from apps.inventory.models import LicenseAssignment

    acrobat = AssetModel.objects.get(name="Acrobat Pro")
    start = date.today()
    rid = employee_client.post(
        "/api/requests",
        {
            "title": "Project",
            "duration": "temporary",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=5)).isoformat(),
            "items": [{"asset_model": str(acrobat.pk), "quantity": 1}],
        },
        content_type=JSON,
    ).json()["id"]
    it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)
    it_client.post(f"/api/requests/{rid}/auto-allocate")
    asset_request = it_client.post(f"/api/requests/{rid}/ready", {}, content_type=JSON).json()
    assert asset_request["status"] == "handed_out"
    employee = User.objects.get(username="employee")

    # Removing the seat on the license page counts as the return.
    assignment = LicenseAssignment.objects.get(license__model=acrobat, user=employee)
    response = it_client.delete(
        f"/api/inventory/licenses/{assignment.license_id}/assignments/{assignment.pk}"
    )
    assert response.status_code == 200, response.content
    assert it_client.get(f"/api/requests/{rid}").json()["status"] == "completed"


def test_catalog_shows_free_seats_to_it(it_client):
    catalog = it_client.get("/api/portal/catalog").json()
    office = next(c for c in catalog if c["code"] == "office-software")
    assert office["kind"] == "software"
    m365 = next(m for m in office["models"] if m["name"] == "365 Business Standard")
    assert m365["available"] == 21


def test_my_licenses_lists_user_and_device_seats(employee_client, it_client):
    from apps.inventory.models import License

    workstation = Asset.objects.filter(model__name="Precision 3680 Tower").first()
    assert workstation is not None
    it_client.post(
        f"/api/inventory/assets/{workstation.pk}/assign",
        {"user": str(User.objects.get(username="employee").pk)},
        content_type=JSON,
    )
    licenses = employee_client.get("/api/portal/my-licenses").json()
    by_name = {entry["model"]["name"]: entry for entry in licenses}
    # Microsoft 365 is assigned to the employee, AutoCAD to the workstation they now use.
    assert by_name["365 Business Standard"]["device"] is None
    assert by_name["AutoCAD LT"]["device"]["inventory_number"] == workstation.inventory_number
    assert "license_key" not in by_name["AutoCAD LT"]
    assert License.objects.filter(model__name="AutoCAD LT").exists()


def test_removing_an_unknown_seat_is_a_404(it_client):
    acrobat = AssetModel.objects.get(name="Acrobat Pro")
    license_id = it_client.post(
        "/api/inventory/licenses", license_payload(acrobat), content_type=JSON
    ).json()["id"]
    response = it_client.delete(f"/api/inventory/licenses/{license_id}/assignments/{uuid.uuid4()}")
    assert response.status_code == 404

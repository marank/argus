from datetime import date, timedelta

from django.test import Client

from apps.accounts.models import User
from apps.inventory.models import Asset
from apps.masterdata.models import AssetModel, Category, Location
from apps.reservations.models import Reservation

JSON = "application/json"


def submit(client, items, duration="temporary", start=None):
    start = start or date.today()
    data = {"title": "Test", "duration": duration, "start_date": start.isoformat(), "items": items}
    if duration == "temporary":
        data["end_date"] = (start + timedelta(days=3)).isoformat()
    return client.post("/api/reservations", data, content_type=JSON)


def prepare(employee_client, it_client, items, duration="temporary", handover_mode="collect", **confirm):
    response = submit(employee_client, items, duration)
    assert response.status_code == 201, response.content
    rid = response.json()["id"]
    it_client.post(f"/api/reservations/{rid}/confirm", {"items": [], **confirm}, content_type=JSON)
    it_client.post(f"/api/reservations/{rid}/auto-allocate")
    response = it_client.post(
        f"/api/reservations/{rid}/ready", {"handover_mode": handover_mode}, content_type=JSON
    )
    assert response.status_code == 200, response.content
    return rid


def laptops():
    return [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 1}]


def lent_allocation(rid):
    return Reservation.objects.get(pk=rid).items.get().allocations.get()


def test_start_date_must_not_be_in_the_past(employee_client):
    response = submit(employee_client, laptops(), start=date.today() - timedelta(days=1))
    assert response.status_code == 409


def test_reserved_device_keeps_its_status(employee_client, it_client):
    rid = prepare(employee_client, it_client, laptops())
    asset = lent_allocation(rid).asset
    payload = it_client.get(f"/api/inventory/assets/{asset.pk}").json()
    body = {
        "model": payload["model"]["id"],
        "status": "in_repair",
        "serial_number": payload["serial_number"],
    }
    response = it_client.put(f"/api/inventory/assets/{asset.pk}", body, content_type=JSON)
    assert response.status_code == 409, response.content
    asset.refresh_from_db()
    assert asset.status == Asset.Status.RESERVED


def test_consumables_only_complete_on_hand_out(employee_client, it_client):
    ink = AssetModel.objects.filter(tracking=AssetModel.Tracking.BULK, consumables__quantity__gt=0).first()
    rid = prepare(employee_client, it_client, [{"asset_model": str(ink.pk), "quantity": 1}])
    response = it_client.post(f"/api/reservations/{rid}/hand-out", {"method": "direct"}, content_type=JSON)
    assert response.json()["status"] == "completed"


def test_return_with_notes_damage_and_record(employee_client, it_client):
    category = str(Category.objects.get(code="laptops").pk)
    rid = prepare(employee_client, it_client, [{"category": category, "quantity": 2}])
    it_client.post(f"/api/reservations/{rid}/hand-out", {"method": "direct"}, content_type=JSON)
    first, second = Reservation.objects.get(pk=rid).items.get().allocations.all()

    response = it_client.post(
        f"/api/reservations/{rid}/return",
        {
            "allocations": [str(first.pk)],
            "notes": "Came back early",
            "allocation_notes": [{"allocation": str(first.pk), "note": "Display cracked"}],
            "damaged": [str(first.pk)],
        },
        content_type=JSON,
    )
    data = response.json()
    assert data["status"] == "handed_out"
    assert len(data["returns"]) == 1 and data["returns"][0]["notes"] == "Came back early"
    first.refresh_from_db()
    assert first.return_note == "Display cracked" and first.asset.status == Asset.Status.IN_REPAIR

    data = it_client.post(f"/api/reservations/{rid}/return", {}, content_type=JSON).json()
    assert data["status"] == "completed" and len(data["returns"]) == 2
    second.refresh_from_db()
    assert second.asset.status == Asset.Status.IN_STOCK


def test_permanent_devices_can_be_taken_back_on_the_request(employee_client, it_client):
    rid = prepare(employee_client, it_client, laptops(), duration="permanent")
    data = it_client.post(f"/api/reservations/{rid}/hand-out", {"method": "direct"}, content_type=JSON).json()
    assert data["status"] == "completed"
    data = it_client.post(f"/api/reservations/{rid}/return", {}, content_type=JSON).json()
    assert data["status"] == "completed"
    allocation = lent_allocation(rid)
    assert allocation.returned_at is not None and allocation.asset.assigned_to is None
    # Nothing is left to take back.
    assert it_client.post(f"/api/reservations/{rid}/return", {}, content_type=JSON).status_code == 409


def test_terminal_names_who_prepared_the_pickup(employee_client, it_client, terminal_client):
    rid = prepare(employee_client, it_client, laptops(), handover_mode="pickup")
    it_user = User.objects.get(username="it")
    staff = terminal_client.get("/api/terminal/staff").json()
    assert it_user.display_name in [s["display_name"] for s in staff]

    sign = {"signature": "data:image/png;base64,AAAA", "notes": ""}
    data = terminal_client.post(f"/api/terminal/pickups/{rid}/sign", sign, content_type=JSON).json()
    assert data["prepared_by"]["username"] == "it"
    assert data["handover"]["handed_out_by"]["username"] == "it"
    assert data["handover"]["recorded_by"]["username"] == "terminal"


def test_terminal_can_name_someone_else_from_it(employee_client, it_client, terminal_client):
    rid = prepare(employee_client, it_client, laptops(), handover_mode="pickup")
    admin = User.objects.get(username="admin")
    employee = User.objects.get(username="employee")
    sign = {"signature": "data:image/png;base64,AAAA", "notes": "", "handed_out_by": str(employee.pk)}
    assert (
        terminal_client.post(f"/api/terminal/pickups/{rid}/sign", sign, content_type=JSON).status_code == 409
    )
    sign["handed_out_by"] = str(admin.pk)
    data = terminal_client.post(f"/api/terminal/pickups/{rid}/sign", sign, content_type=JSON).json()
    assert data["handover"]["handed_out_by"]["username"] == "admin"


def test_terminal_with_a_site_lists_only_its_pickups(employee_client, it_client, terminal_client):
    north = Location.objects.create(name="North", kind=Location.Kind.SITE)
    north_desk = Location.objects.create(name="Desk", parent=north, is_pickup_point=True)
    south = Location.objects.create(name="South", kind=Location.Kind.SITE, is_pickup_point=True)
    here = prepare(
        employee_client, it_client, laptops(), handover_mode="pickup", pickup_location=str(north_desk.pk)
    )
    there = prepare(
        employee_client, it_client, laptops(), handover_mode="pickup", pickup_location=str(south.pk)
    )

    terminal = User.objects.get(username="terminal")
    terminal.terminal_location = north
    terminal.save()
    ids = {p["id"] for p in terminal_client.get("/api/terminal/pickups").json()}
    assert here in ids and there not in ids
    assert terminal_client.get(f"/api/terminal/pickups/{there}").status_code == 404

    # IT staff testing the terminal still see everything.
    ids = {p["id"] for p in it_client.get("/api/terminal/pickups").json()}
    assert {here, there} <= ids


def test_device_license_goes_onto_one_of_the_requesters_devices(employee_client, it_client):
    autocad = AssetModel.objects.get(name="AutoCAD LT")
    response = submit(
        employee_client, [{"asset_model": str(autocad.pk), "quantity": 1}], duration="permanent"
    )
    rid, item = response.json()["id"], response.json()["items"][0]
    it_client.post(f"/api/reservations/{rid}/confirm", {"items": []}, content_type=JSON)
    candidates = it_client.get(f"/api/reservations/items/{item['id']}/candidates").json()
    license = candidates["licenses"][0]
    assert license["assign_to"] == "device"
    mine = Asset.objects.filter(assigned_to__username="employee").first()
    assert mine and str(mine.pk) in [d["id"] for d in candidates["devices"]]

    foreign = Asset.objects.exclude(assigned_to__username="employee").first()
    body = {"item": item["id"], "license": license["id"], "asset": str(foreign.pk)}
    assert it_client.post(f"/api/reservations/{rid}/allocations", body, content_type=JSON).status_code == 409
    body["asset"] = str(mine.pk)
    data = it_client.post(f"/api/reservations/{rid}/allocations", body, content_type=JSON).json()
    seat = data["items"][0]["allocations"][0]["license"]
    assert seat["device"]["id"] == str(mine.pk)

    # While the request is being prepared the seat cannot be removed on the license page.
    from apps.inventory.models import LicenseAssignment

    assignment = LicenseAssignment.objects.get(license_id=license["id"], asset=mine)
    url = f"/api/inventory/licenses/{license['id']}/assignments/{assignment.pk}"
    assert it_client.delete(url).status_code == 409

    # Cancelling the request frees the seat again.
    it_client.post(f"/api/reservations/{rid}/cancel")
    assert not LicenseAssignment.objects.filter(pk=assignment.pk).exists()


def test_it_staff_not_a_terminal_cannot_be_impersonated(demo):
    """Only IT staff and terminal accounts reach the staff list."""
    client = Client()
    client.login(username="employee", password="argus-demo")
    assert client.get("/api/terminal/staff").status_code == 403

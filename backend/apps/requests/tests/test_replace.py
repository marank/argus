from datetime import timedelta

from django.core import mail
from django.utils import timezone

from apps.accounts.models import Team, User
from apps.activity.models import Activity, ActivityKind
from apps.core.models import Notification
from apps.inventory.models import AssetStatus
from apps.masterdata.models import Category
from apps.requests.models import AssetRequest, AssetRequestAllocation, AssetRequestStatus
from apps.requests.tests.flow import JSON, laptops, prepare, submit
from apps.requests.tests.test_approvals import approval_setup, approver_client
from apps.requests.tests.test_approvals import request as approval_request
from apps.requests.tests.test_direct_hand_out import employee, in_stock, post

__all__ = ["approval_setup", "approver_client"]


def headset() -> dict[str, object]:
    return {"category": str(Category.objects.get(code="headsets").pk), "quantity": 1}


def replace(client, old: AssetRequest, items, **extra):
    data = {
        "title": "Replaced",
        "duration": "permanent",
        "start_date": old.start_date.isoformat(),
        "requester": str(old.requester_id),
        "items": items,
        "replaces": str(old.pk),
        **extra,
    }
    return client.post("/api/requests", data, content_type=JSON)


def confirmed_with_laptop(employee_client, it_client) -> AssetRequest:
    rid = submit(employee_client, laptops()).json()["id"]
    it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)
    it_client.post(f"/api/requests/{rid}/auto-allocate")
    old = AssetRequest.objects.get(pk=rid)
    assert AssetRequestAllocation.objects.filter(item__asset_request=old).count() == 1
    return old


def test_replacing_keeps_what_was_allocated_and_cancels_quietly(employee_client, it_client):
    old = confirmed_with_laptop(employee_client, it_client)
    old.assigned_team = Team.objects.create(name="IT-Support")
    old.pickup_at = timezone.now() - timedelta(days=1)
    old.save()
    laptop = AssetRequestAllocation.objects.get(item__asset_request=old).asset
    assert laptop is not None
    Notification.objects.all().delete()
    Activity.objects.all().delete()

    response = replace(it_client, old, [*laptops(), headset()])
    assert response.status_code == 201, response.content
    body = response.json()

    # The new request is confirmed like the old one and has the laptop allocated again.
    assert body["status"] == "confirmed"
    assert body["follows"]["number"] == old.number
    assert body["assigned_team"]["name"] == "IT-Support"
    # A pickup date that has passed is planned anew.
    assert body["pickup_at"] is None
    assert [i["quantity_confirmed"] for i in body["items"]] == [1, 1]
    assert body["items"][0]["allocations"][0]["asset"]["id"] == str(laptop.pk)
    laptop.refresh_from_db()
    assert laptop.status == AssetStatus.RESERVED

    old.refresh_from_db()
    assert old.status == AssetRequestStatus.CANCELLED
    replaced = old.events.get(kind="replaced")
    assert replaced.data == {"by": body["number"]}
    # Nobody is told: neither the employee of a cancellation nor IT of a new request.
    assert not Notification.objects.exists()
    # One step in the activity log.
    assert list(Activity.objects.values_list("kind", flat=True)) == [ActivityKind.REQUEST_REPLACED]


def test_what_no_longer_fits_is_given_back(employee_client, it_client):
    old = confirmed_with_laptop(employee_client, it_client)
    laptop = AssetRequestAllocation.objects.get(item__asset_request=old).asset
    assert laptop is not None

    response = replace(it_client, old, [headset()])
    assert response.status_code == 201, response.content
    assert response.json()["items"][0]["allocations"] == []
    laptop.refresh_from_db()
    assert laptop.status == AssetStatus.IN_STOCK


def test_a_submitted_request_stays_to_be_confirmed(employee_client, it_client):
    old = AssetRequest.objects.get(pk=submit(employee_client, laptops()).json()["id"])
    response = replace(it_client, old, [*laptops(), headset()])
    assert response.status_code == 201, response.content
    assert response.json()["status"] == "submitted"


def test_a_direct_hand_out_picks_its_devices_again(it_client):
    first, second = in_stock(2)
    old_id = post(it_client, assets=[str(first.pk)]).json()["id"]
    old = AssetRequest.objects.get(pk=old_id)

    response = post(it_client, assets=[str(first.pk), str(second.pk)], replaces=old_id)
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["origin"] == "direct"
    assert sorted(a["asset"]["id"] for i in body["items"] for a in i["allocations"]) == sorted(
        [str(first.pk), str(second.pk)]
    )
    old.refresh_from_db()
    assert old.status == AssetRequestStatus.CANCELLED
    assert old.events.filter(kind="replaced").exists()


def test_only_for_the_same_employee_and_nothing_changes_otherwise(employee_client, it_client):
    old = confirmed_with_laptop(employee_client, it_client)
    count = AssetRequest.objects.count()
    other = User.objects.exclude(pk=old.requester_id).filter(is_active=True).first()
    assert other is not None
    response = replace(it_client, old, laptops(), requester=str(other.pk))
    assert response.status_code == 409
    old.refresh_from_db()
    assert old.status == AssetRequestStatus.CONFIRMED
    assert AssetRequest.objects.count() == count
    assert AssetRequestAllocation.objects.filter(item__asset_request=old).count() == 1


def test_not_after_the_hand_out_and_not_by_employees(employee_client, it_client):
    old = confirmed_with_laptop(employee_client, it_client)
    response = replace(employee_client, old, laptops())
    assert response.status_code == 409

    old.status = AssetRequestStatus.HANDED_OUT
    old.save()
    assert replace(it_client, old, laptops()).status_code == 409
    assert employee().pk == old.requester_id


def test_a_request_waiting_for_approval_waits_again(
    approval_setup, employee_client, approver_client, it_client, django_capture_on_commit_callbacks
):
    old = AssetRequest.objects.get(pk=approval_request(employee_client, "laptops")["id"])
    assert old.status == AssetRequestStatus.PENDING_APPROVAL
    mail.outbox.clear()

    with django_capture_on_commit_callbacks(execute=True):
        response = replace(it_client, old, [*laptops(), headset()])
    assert response.status_code == 201, response.content
    body = response.json()
    assert (body["status"], body["approval"]) == ("pending_approval", "pending")
    # The department is asked about the new request; the old one is gone from its list.
    assert [m.to for m in mail.outbox] == [["sales@example.com"]]
    pending = approver_client.get("/api/approvals").json()["items"]
    assert [r["id"] for r in pending] == [body["id"]]


def test_an_approval_already_given_stays(approval_setup, employee_client, approver_client, it_client):
    old_id = approval_request(employee_client, "laptops")["id"]
    approver_client.post(f"/api/approvals/{old_id}/approve", {"comment": "Fine"}, content_type=JSON)
    old = AssetRequest.objects.get(pk=old_id)

    body = replace(it_client, old, [*laptops(), headset()]).json()
    assert (body["status"], body["approval"]) == ("submitted", "approved")
    assert body["approver"]["username"] == "sales"
    assert body["approval_comment"] == "Fine"


def test_a_request_waiting_for_approval_does_not_become_a_direct_hand_out(
    approval_setup, employee_client, it_client
):
    old_id = approval_request(employee_client, "laptops")["id"]
    (laptop,) = in_stock(1)
    response = post(it_client, assets=[str(laptop.pk)], replaces=old_id)
    assert response.status_code == 409
    assert AssetRequest.objects.get(pk=old_id).status == AssetRequestStatus.PENDING_APPROVAL


def test_a_ready_request_keeps_its_devices_and_handover(employee_client, it_client):
    old = AssetRequest.objects.get(pk=prepare(employee_client, it_client, laptops()))
    assert old.status == AssetRequestStatus.READY
    laptop = AssetRequestAllocation.objects.get(item__asset_request=old).asset
    assert laptop is not None

    body = replace(it_client, old, [*laptops(), headset()]).json()
    # Back in preparation: the headset is still to be allocated.
    assert body["status"] == "confirmed"
    assert body["items"][0]["allocations"][0]["asset"]["id"] == str(laptop.pk)
    assert body["handover_mode"] == old.handover_mode
    assert body["pickup_at"] is not None
    assert body["pickup_location"]["id"] == str(old.pickup_location_id)

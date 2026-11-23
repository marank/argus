"""Findings of the production readiness audit: leaks, unchecked ids and unbounded input."""

import uuid

import pytest
from django.test import Client

from apps.accounts.models import Department, User
from apps.core.exceptions import BusinessError
from apps.inventory.services.availability import pool_assets
from apps.masterdata.models import Category
from apps.requests.models import AssetRequest, AssetRequestStatus, Handover
from apps.requests.services import workflow

from .flow import laptops, submit
from .test_handover import SIGNATURE, ready_pickup

JSON = "application/json"
# Fields of the full request that are IT-internal and have no place on a shared terminal.
INTERNAL = {
    "notes",
    "it_comment",
    "approval_comment",
    "follows",
    "events",
    "created_by",
    "assigned_team",
    "assignee",
    "approver",
    "reminded_by",
}


def sign(client, asset_request, **data):
    payload = {"signature": SIGNATURE, "received_by_name": "Max Colleague", **data}
    return client.post(f"/api/terminal/pickups/{asset_request.pk}/sign", payload, content_type=JSON)


def test_terminal_pickup_shows_no_internal_details(terminal_client, it_client):
    asset_request = ready_pickup()
    asset_request.notes = "Private note"
    asset_request.it_comment = "Internal comment"
    asset_request.save()
    for client in (terminal_client, it_client):
        detail = client.get(f"/api/terminal/pickups/{asset_request.pk}").json()
        assert not INTERNAL & detail.keys()
        assert "Private note" not in str(detail)
        assert "Internal comment" not in str(detail)
        allocation = detail["items"][0]["allocations"][0]
        assert "allocated_by" not in allocation
        # What the terminal needs to show the pickup is still there.
        assert allocation["asset"]["inventory_number"]
        assert detail["requester"]["display_name"] == asset_request.requester.display_name

    response = sign(terminal_client, asset_request)
    assert response.status_code == 200, response.content
    body = response.json()
    assert not INTERNAL & body.keys()
    assert body["handover"]["received_by_name"] == "Max Colleague"


def test_unknown_or_inactive_collector_is_refused(terminal_client):
    asset_request = ready_pickup()
    response = sign(terminal_client, asset_request, received_by=str(uuid.uuid4()))
    assert response.status_code == 409
    assert "collecting" in response.json()["detail"]

    former = User.objects.create_user("former", first_name="Fred", last_name="Former", is_active=False)
    for user in (User.objects.get(username="terminal"), former):
        response = sign(terminal_client, asset_request, received_by=str(user.pk))
        assert response.status_code == 409, user
    assert not Handover.objects.exists()

    colleague = User.objects.get(username="admin")
    response = sign(terminal_client, asset_request, received_by=str(colleague.pk), received_by_name="")
    assert response.status_code == 200, response.content
    assert response.json()["handover"]["received_by_name"] == colleague.display_name


def test_handed_out_by_must_be_active_it_staff(terminal_client):
    asset_request = ready_pickup()
    inactive = User.objects.get(username="admin")
    inactive.is_active = False
    inactive.save()
    for user_id in (uuid.uuid4(), inactive.pk, User.objects.get(username="terminal").pk):
        response = sign(terminal_client, asset_request, handed_out_by=str(user_id))
        assert response.status_code == 409
    assert not Handover.objects.exists()


def test_signing_twice_is_a_conflict_not_an_error(terminal_client, it_client):
    asset_request = ready_pickup()
    assert sign(terminal_client, asset_request).status_code == 200
    # The terminal no longer lists it; IT handing it out again is refused cleanly.
    assert sign(terminal_client, asset_request).status_code == 404
    response = it_client.post(
        f"/api/requests/{asset_request.pk}/hand-out", {"method": "direct"}, content_type=JSON
    )
    assert response.status_code == 409
    # Even a stale instance (as a concurrent request would have had) gets a clean refusal.
    stale = AssetRequest.objects.get(pk=asset_request.pk)
    stale.status = AssetRequestStatus.READY
    with pytest.raises(BusinessError, match="already been handed out"):
        workflow.hand_out(stale, User.objects.get(username="it"))
    assert Handover.objects.filter(asset_request=asset_request).count() == 1


def test_allocation_still_stops_at_the_confirmed_quantity(employee_client, it_client):
    rid = submit(employee_client, laptops()).json()["id"]
    it_client.post(f"/api/requests/{rid}/confirm", {"items": []}, content_type=JSON)
    item = AssetRequest.objects.get(pk=rid).items.get()
    first, second = pool_assets(model_id=None, category_id=item.category_id)[:2]
    url = f"/api/requests/{rid}/allocations"
    response = it_client.post(url, {"item": str(item.pk), "asset": str(first.pk)}, content_type=JSON)
    assert response.status_code == 200, response.content
    response = it_client.post(url, {"item": str(item.pk), "asset": str(second.pk)}, content_type=JSON)
    assert response.status_code == 409
    assert item.allocations.count() == 1


def test_approving_someone_elses_request_reveals_nothing(employee_client):
    """Without being an approver, approving a request of another department is a plain 404."""
    Category.objects.filter(code="laptops").update(requires_approval=True)
    sales_client = Client()
    sales_client.login(username="sales", password="argus-demo")
    rid = submit(sales_client, laptops()).json()["id"]
    Department.objects.get(name="Sales").approvers.add(User.objects.get(username="admin"))
    # Also once IT moved it on: the status must not show through.
    AssetRequest.objects.filter(pk=rid).update(status=AssetRequestStatus.READY)

    for action in ("approve", "decline"):
        response = employee_client.post(
            f"/api/approvals/{rid}/{action}", {"comment": "No"}, content_type=JSON
        )
        assert response.status_code == 404, response.content
        assert "Ready" not in response.json()["detail"]
    assert (
        employee_client.post(f"/api/approvals/{uuid.uuid4()}/approve", {}, content_type=JSON).status_code
        == 404
    )


def test_very_long_search_terms_are_capped(it_client, terminal_client):
    q = " ".join(f"word{i}" for i in range(1500))
    for client, url in (
        (it_client, "/api/requests"),
        (it_client, "/api/approvals"),
        (terminal_client, "/api/terminal/pickups"),
        (terminal_client, "/api/terminal/people"),
    ):
        response = client.get(url, {"q": q})
        assert response.status_code == 200, (url, response.content[:200])


def test_search_ignores_words_beyond_the_cap(terminal_client):
    asset_request = ready_pickup()
    # The first words all match; the many words after them are ignored.
    q = " ".join([asset_request.requester.last_name] * 10 + ["zzz"] * 50)
    ids = [p["id"] for p in terminal_client.get("/api/terminal/pickups", {"q": q}).json()]
    assert ids == [str(asset_request.pk)]

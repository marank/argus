"""A step of a request is one row, however many devices it covers."""

from uuid import UUID

from django.utils import timezone

from apps.accounts.models import User
from apps.activity.models import Activity
from apps.inventory.models import Asset, AssetStatus
from apps.masterdata.models import Category
from apps.requests.models import AssetRequest
from apps.requests.tests.flow import JSON, laptops, prepare, submit


def test_hand_out_and_return_are_one_row_each(employee_client, it_client, fresh):
    laptops = [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 2}]
    rid = prepare(employee_client, it_client, laptops)
    response = it_client.post(f"/api/requests/{rid}/hand-out", {"method": "direct"}, content_type=JSON)
    assert response.status_code == 200, response.content

    hand_out = Activity.objects.get(kind="request_handed_out")
    request = AssetRequest.objects.get(pk=rid)
    assert (hand_out.area, hand_out.subject_id, hand_out.quantity) == ("requests", request.pk, 2)
    assert hand_out.subject_label == f"{request.number} – {request.title}"
    assert hand_out.actor is not None and hand_out.actor.username == "it"
    assert hand_out.related_user_id == request.requester_id
    # The devices' own entries are part of that row.
    assert not Activity.objects.filter(area="assets").exists()

    it_client.post(f"/api/requests/{rid}/return", {}, content_type=JSON)
    assert Activity.objects.filter(kind="request_returned", quantity=2).count() == 1
    assert Activity.objects.filter(kind="request_completed").count() == 1
    assert not Activity.objects.filter(area__in=("assets", "consumables")).exists()


def in_stock(count: int) -> list[Asset]:
    return list(Asset.objects.filter(status=AssetStatus.IN_STOCK).order_by("inventory_number")[:count])


def test_direct_hand_out_and_quick_assignment_are_one_row_each(it_client, fresh):
    requester = str(User.objects.get(username="employee").pk)
    first, second, third = in_stock(3)
    direct = it_client.post(
        "/api/requests/direct",
        {
            "title": "New colleague",
            "duration": "permanent",
            "start_date": str(timezone.localdate()),
            "requester": requester,
            "assets": [str(first.pk), str(second.pk)],
        },
        content_type=JSON,
    )
    assert direct.status_code == 201, direct.content
    quick = it_client.post(
        "/api/requests/quick",
        {"asset": str(third.pk), "requester": requester, "duration": "permanent"},
        content_type=JSON,
    )
    assert quick.status_code == 201, quick.content

    rows = list(Activity.objects.order_by("occurred_at").values_list("kind", "quantity", "subject_id"))
    assert rows == [
        ("request_direct", 2, UUID(direct.json()["id"])),
        ("request_quick", 1, UUID(quick.json()["id"])),
    ]


def test_each_allocation_and_removal_is_a_row_of_its_own(employee_client, it_client, admin_client, fresh):
    """The request's history lists the result; the activity log has every step and who took it."""
    response = submit(
        employee_client, [{"category": str(Category.objects.get(code="laptops").pk), "quantity": 2}]
    )
    rid = response.json()["id"]
    url = f"/api/requests/{rid}"
    it_client.post(f"{url}/confirm", {}, content_type=JSON)
    item = AssetRequest.objects.get(pk=rid).items.get()
    first, second = (
        Asset.objects.filter(model__category=item.category, status=AssetStatus.IN_STOCK)
        .select_related("model")
        .order_by("inventory_number")[:2]
    )
    body = it_client.post(
        f"{url}/allocations", {"item": str(item.pk), "asset": str(first.pk)}, content_type=JSON
    ).json()
    admin_client.post(
        f"{url}/allocations", {"item": str(item.pk), "asset": str(second.pk)}, content_type=JSON
    )
    admin_client.delete(f"{url}/allocations/{body['items'][0]['allocations'][0]['id']}")

    rows = it_client.get("/api/activities", {"subject": rid, "ordering": "occurred_at"}).json()["items"]
    assert [(r["kind"], r["actor"]["username"], r["detail"]) for r in rows] == [
        ("request_created", "employee", ""),
        ("request_confirmed", "it", ""),
        ("request_allocated", "it", f"{first.inventory_number} · {first.model.full_name}"),
        ("request_allocated", "admin", f"{second.inventory_number} · {second.model.full_name}"),
        ("request_released", "admin", f"{first.inventory_number} · {first.model.full_name}"),
    ]
    assert {r["subject_id"] for r in rows} == {rid}


def test_automatic_allocation_says_so(employee_client, it_client, fresh):
    rid = prepare(employee_client, it_client, laptops())
    allocated = Activity.objects.get(kind="request_allocated", subject_id=rid)
    assert allocated.detail.endswith("(automatically)")
    assert allocated.actor is not None and allocated.actor.username == "it"

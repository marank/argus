"""A step of a request is one row, however many devices it covers."""

from apps.activity.models import Activity
from apps.masterdata.models import Category
from apps.requests.models import AssetRequest
from apps.requests.tests.flow import JSON, prepare


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

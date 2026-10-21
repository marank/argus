import pytest
from django.core.exceptions import ValidationError
from django.test import Client

from apps.accounts.models import Team
from apps.masterdata.models import Category, Location


@pytest.mark.parametrize("model", [Category, Location])
def test_parent_cannot_be_the_node_itself_or_below_it(demo, model):
    root = model.objects.create(name="Root", code="t-root")
    child = model.objects.create(name="Child", code="t-child", parent=root)
    grandchild = model.objects.create(name="Grandchild", code="t-grandchild", parent=child)

    for parent in (root, grandchild):
        root.parent = parent
        with pytest.raises(ValidationError) as error:
            root.full_clean()
        assert "parent" in error.value.message_dict

    # Moving a branch elsewhere stays possible.
    grandchild.parent = root
    grandchild.full_clean()


def test_a_loop_in_the_database_does_not_hang(demo):
    a = Category.objects.create(name="A", code="t-a")
    b = Category.objects.create(name="B", code="t-b", parent=a)
    Category.objects.filter(pk=a.pk).update(parent=b)
    a.refresh_from_db()
    assert [c.name for c in a.ancestors()] == ["B"]
    assert a.descendant_ids() == {a.pk, b.pk}

    x = Location.objects.create(name="X")
    y = Location.objects.create(name="Y", parent=x)
    Location.objects.filter(pk=x.pk).update(parent=y)
    x.refresh_from_db()
    assert x.full_name == "Y / X"
    assert x.descendant_ids() == {x.pk, y.pk}


def test_categories_and_locations_can_be_created_through_the_api(demo):
    # The UUID is set before saving; clean() must not look up the unsaved record (was a 500).
    admin = Client()
    admin.login(username="admin", password="argus-demo")
    team = Team.objects.create(name="Logistics IT")
    payload = {
        "name": "MDEs",
        "item_name": "MDE",
        "kind": "hardware",
        "code": "MDE",
        "parent": None,
        "description": "",
        "icon": "barcode",
        "number_sequence": None,
        "team": str(team.pk),
        "is_requestable": True,
        "allow_any_model": True,
        "requires_approval": False,
        "sort_order": 0,
    }
    response = admin.post("/api/masterdata/categories", payload, content_type="application/json")
    assert response.status_code == 201, response.content
    child = {**payload, "name": "Ring scanners", "code": "MDE-R", "parent": response.json()["id"]}
    response = admin.post("/api/masterdata/categories", child, content_type="application/json")
    assert response.status_code == 201, response.content

    root = Location.objects.first()
    response = admin.post(
        "/api/masterdata/locations",
        {"name": "Store room", "code": "t-store", "parent": str(root.pk)},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content

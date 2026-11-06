import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Department, Team
from apps.masterdata.models import Category, Location


@pytest.mark.parametrize("model", [Category, Location, Department])
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


def test_categories_and_locations_can_be_created_through_the_api(admin_client):
    # The UUID is set before saving; clean() must not look up the unsaved record (was a 500).
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
        "model_choice": "any_or_specific",
        "requires_approval": False,
        "sort_order": 0,
    }
    response = admin_client.post("/api/masterdata/categories", payload, content_type="application/json")
    assert response.status_code == 201, response.content
    child = {**payload, "name": "Ring scanners", "code": "MDE-R", "parent": response.json()["id"]}
    response = admin_client.post("/api/masterdata/categories", child, content_type="application/json")
    assert response.status_code == 201, response.content

    root = Location.objects.first()
    assert root is not None
    response = admin_client.post(
        "/api/masterdata/locations",
        {"name": "Store room", "code": "t-store", "parent": str(root.pk)},
        content_type="application/json",
    )
    assert response.status_code == 201, response.content


def test_category_code_is_optional_but_unique_when_given(admin_client):
    for name in ("Headsets", "Docking stations"):
        response = admin_client.post(
            "/api/masterdata/categories", {"name": name}, content_type="application/json"
        )
        assert response.status_code == 201, response.content
        assert response.json()["code"] == ""

    coded = Category.objects.exclude(code="").first()
    assert coded is not None
    taken = coded.code
    response = admin_client.post(
        "/api/masterdata/categories", {"name": "Copy", "code": taken}, content_type="application/json"
    )
    assert response.status_code == 422, response.content
    assert "code" in response.json()["errors"]


def test_categories_list_parents_before_their_subcategories(admin_client):
    mde = Category.objects.create(name="MDEs", code="t-mde", sort_order=50)
    Category.objects.create(name="Handgriffe", code="t-handles", parent=mde, sort_order=0)
    Category.objects.create(name="Dockingstationen", code="t-docks", parent=mde, sort_order=0)
    Category.objects.create(name="Laptops 2", code="t-laptops", sort_order=40)

    for ordering in ("", "kind,tree_position"):
        items = admin_client.get(f"/api/masterdata/categories?page_size=200&ordering={ordering}").json()[
            "items"
        ]
        names = [" / ".join(c["path"]) for c in items if c["code"].startswith("t-")]
        assert names == ["Laptops 2", "MDEs", "MDEs / Dockingstationen", "MDEs / Handgriffe"]
        # Every subcategory directly follows its parent's branch.
        paths = [" / ".join(c["path"]) for c in items]
        for index, path in enumerate(paths[1:], 1):
            if " / " in path:
                assert paths[index - 1].startswith(path.rsplit(" / ", 1)[0])


def test_categories_show_the_team_and_approval_that_apply(admin_client):
    team = Team.objects.create(name="Logistics IT")
    mde = Category.objects.create(name="MDEs", code="t-mde", team=team, requires_approval=True)
    docks = Category.objects.create(name="Docks", code="t-docks", parent=mde)
    cradles = Category.objects.create(name="Cradles", code="t-cradles", parent=docks)

    body = admin_client.get(f"/api/masterdata/categories/{cradles.pk}").json()
    assert body["team"] is None and body["effective_team"]["id"] == str(team.pk)
    assert body["requires_approval"] is False and body["needs_approval"] is True
    body = admin_client.get(f"/api/masterdata/categories/{mde.pk}").json()
    assert body["effective_team"]["id"] == str(team.pk) and body["needs_approval"] is True


def test_the_default_team_applies_where_nothing_else_does(admin_client):
    from apps.masterdata.models import AssetModel

    support = Team.objects.create(name="Front desk", is_default=True)
    hardware = Team.objects.create(name="Hardware")
    mde = Category.objects.create(name="MDEs", code="t-mde")
    model = AssetModel.objects.filter(tracking="serialized").first()
    assert model is not None
    model.category, model.team = mde, None
    model.save()

    assert admin_client.get(f"/api/masterdata/categories/{mde.pk}").json()["effective_team"]["id"] == str(
        support.pk
    )
    assert admin_client.get(f"/api/masterdata/models/{model.pk}").json()["effective_team"]["id"] == str(
        support.pk
    )
    mde.team = hardware
    mde.save()
    body = admin_client.get(f"/api/masterdata/models/{model.pk}").json()
    assert body["team"] is None and body["effective_team"]["id"] == str(hardware.pk)


def test_departments_get_an_icon_from_the_choices(admin_client):
    operations = Department.objects.create(name="Operations")
    assert operations.icon == Department.Icon.BUILDING

    payload = {"name": "Support", "icon": "headset", "parent": str(operations.pk)}
    response = admin_client.post("/api/accounts/departments", payload, content_type="application/json")
    assert response.status_code == 201, response.content
    assert response.json()["icon"] == "headset"

    response = admin_client.post(
        "/api/accounts/departments",
        {**payload, "name": "Shoes", "icon": "rocket"},
        content_type="application/json",
    )
    assert response.status_code == 422

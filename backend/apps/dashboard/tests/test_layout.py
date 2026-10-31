from apps.accounts.models import User

JSON = "application/json"


def test_dashboard_layout_is_saved_per_user(it_client):
    layout = {
        "widgets": [
            {
                "id": "requests",
                "visible": True,
                "size": "medium",
                "height": "small",
                "hidden_cards": ["overdue"],
                "card_order": ["ready", "to_confirm"],
                "options": {},
            },
            {
                "id": "mine",
                "visible": False,
                "size": "large",
                "height": "auto",
                "hidden_cards": [],
                "card_order": [],
                "options": {"text": "Call Paul"},
            },
            {
                # A further instance names the widget it shows.
                "id": "week~a1b2c3",
                "widget": "week",
                "visible": True,
                "size": "large",
                "height": "auto",
                "hidden_cards": [],
                "card_order": [],
                "options": {"title": "Counter", "kinds": ["pickup", "return"]},
            },
        ]
    }
    response = it_client.patch("/api/auth/me", {"dashboard_settings": layout}, content_type=JSON)
    assert response.status_code == 200, response.content
    # The first instance of a widget has no "widget"; the API sends it as null.
    expected = {"widgets": [{"widget": None, **widget} for widget in layout["widgets"]]}
    assert response.json()["dashboard_settings"] == expected
    assert it_client.get("/api/auth/me").json()["dashboard_settings"] == expected


def test_dashboard_layout_drops_malformed_entries(it_client):
    response = it_client.patch(
        "/api/auth/me",
        {
            "dashboard_settings": {
                "widgets": [
                    {
                        "id": "requests",
                        "size": "huge",
                        "height": "endless",
                        "hidden_cards": ["a", 3, "a"],
                        "card_order": ["b", "a", "b", ""],
                        "options": {"text": "x" * 11_000},
                    },
                    {"id": "requests", "visible": False},
                    {"visible": True},
                    "nonsense",
                ]
            }
        },
        content_type=JSON,
    )
    assert response.status_code == 200, response.content
    assert response.json()["dashboard_settings"] == {
        "widgets": [
            {
                "id": "requests",
                "widget": None,
                "visible": True,
                "size": "large",
                "height": "auto",
                "hidden_cards": ["a"],
                "card_order": ["b", "a"],
                # Too large for a widget's settings.
                "options": {},
            }
        ]
    }


def test_empty_layout_restores_the_default(it_client):
    it_client.patch(
        "/api/auth/me",
        {"dashboard_settings": {"widgets": [{"id": "mine", "visible": False}]}},
        content_type=JSON,
    )
    response = it_client.patch("/api/auth/me", {"dashboard_settings": {}}, content_type=JSON)
    assert response.json()["dashboard_settings"] == {"widgets": []}
    assert User.objects.get(username="it").dashboard_settings == {}


def test_layouts_saved_before_a_field_existed_get_its_default(it_client):
    User.objects.filter(username="it").update(
        dashboard_settings={"widgets": [{"id": "requests", "visible": True, "size": "medium"}]}
    )
    assert it_client.get("/api/auth/me").json()["dashboard_settings"] == {
        "widgets": [
            {
                "id": "requests",
                "widget": None,
                "visible": True,
                "size": "medium",
                "height": "auto",
                "hidden_cards": [],
                "card_order": [],
                "options": {},
            }
        ]
    }


def test_widget_data_for_it(it_client):
    for path in ("my-tasks", "overdue-returns", "team-load", "request-trend"):
        response = it_client.get(f"/api/dashboard/widgets/{path}")
        assert response.status_code == 200, (path, response.content)
    assert len(it_client.get("/api/dashboard/widgets/request-trend").json()) == 12

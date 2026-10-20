from apps.accounts.models import User

JSON = "application/json"


def test_dashboard_layout_is_saved_per_user(it_client):
    layout = {
        "widgets": [
            {
                "id": "requests",
                "visible": True,
                "size": "medium",
                "hidden_cards": ["overdue"],
                "card_order": ["ready", "to_approve"],
            },
            {"id": "mine", "visible": False, "size": "large", "hidden_cards": [], "card_order": []},
        ]
    }
    response = it_client.patch("/api/auth/me", {"dashboard_settings": layout}, content_type=JSON)
    assert response.status_code == 200, response.content
    assert response.json()["dashboard_settings"] == layout
    assert it_client.get("/api/auth/me").json()["dashboard_settings"] == layout


def test_dashboard_layout_drops_malformed_entries(it_client):
    response = it_client.patch(
        "/api/auth/me",
        {
            "dashboard_settings": {
                "widgets": [
                    {
                        "id": "requests",
                        "size": "huge",
                        "hidden_cards": ["a", 3, "a"],
                        "card_order": ["b", "a", "b", ""],
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
                "visible": True,
                "size": "large",
                "hidden_cards": ["a"],
                "card_order": ["b", "a"],
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
    assert response.json()["dashboard_settings"] == {}
    assert User.objects.get(username="it").dashboard_settings == {}

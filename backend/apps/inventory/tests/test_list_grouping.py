"""Orderings the list tables group their rows by: each group's rows come together."""


def contiguous(keys: list[str | None]) -> bool:
    """Whether every key's rows follow each other."""
    seen: list[str | None] = []
    for key in keys:
        if not seen or seen[-1] != key:
            if key in seen:
                return False
            seen.append(key)
    return True


def test_devices_group_by_location_and_assignee(it_client):
    for ordering, key in (
        ("location__name,location_id", "location"),
        ("assigned_to__last_name,assigned_to__first_name,assigned_to_id", "assigned_to"),
        ("model__manufacturer__name,model__name,model_id", "model"),
    ):
        items = it_client.get(f"/api/inventory/assets?page_size=200&ordering={ordering}").json()["items"]
        keys = [(item[key] or {}).get("id") for item in items]
        assert contiguous(keys), ordering

    # The ordering applies: the models come by manufacturer.
    items = it_client.get("/api/inventory/assets?page_size=200&ordering=model__manufacturer__name").json()[
        "items"
    ]
    names = [item["model"]["full_name"] for item in items]
    assert len(set(names)) > 1
    assert names != [
        item["model"]["full_name"]
        for item in it_client.get("/api/inventory/assets?page_size=200").json()["items"]
    ]


def test_the_event_log_sorts_newest_first_and_by_kind(it_client):
    newest = it_client.get("/api/inventory/events?page_size=200").json()["items"]
    times = [event["occurred_at"] for event in newest]
    assert times == sorted(times, reverse=True)

    by_kind = it_client.get("/api/inventory/events?page_size=200&ordering=kind,-occurred_at").json()["items"]
    assert contiguous([event["kind"] for event in by_kind])

    # Fields not offered for sorting are ignored.
    ignored = it_client.get("/api/inventory/events?page_size=200&ordering=description").json()["items"]
    assert [event["id"] for event in ignored] == [event["id"] for event in newest]


def test_devices_filter_by_purchase_date_and_supplier(it_client):
    items = it_client.get("/api/inventory/assets?page_size=200").json()["items"]
    dated = sorted(item["purchase_date"] for item in items if item["purchase_date"])
    middle = dated[len(dated) // 2]
    later = it_client.get(f"/api/inventory/assets?page_size=200&purchase_from={middle}").json()["items"]
    earlier = it_client.get(f"/api/inventory/assets?page_size=200&purchase_until={middle}").json()["items"]
    assert later
    assert all(item["purchase_date"] >= middle for item in later)
    assert earlier
    assert all(item["purchase_date"] <= middle for item in earlier)

    supplied = next(item for item in items if item.get("supplier"))
    supplier = supplied["supplier"]["id"]
    same = it_client.get(f"/api/inventory/assets?page_size=200&supplier={supplier}").json()["items"]
    assert same
    assert all(item["supplier"]["id"] == supplier for item in same)


def test_list_filters_take_several_values(it_client):
    items = it_client.get("/api/inventory/assets?page_size=200").json()["items"]
    models = sorted({item["model"]["id"] for item in items})[:2]
    query = "&".join(f"model={pk}" for pk in models)
    found = it_client.get(f"/api/inventory/assets?page_size=200&{query}").json()["items"]
    assert {item["model"]["id"] for item in found} == set(models)

    categories = sorted({item["category"]["id"] for item in items})[:2]
    query = "&".join(f"category={pk}" for pk in categories)
    found = it_client.get(f"/api/inventory/assets?page_size=200&{query}").json()["items"]
    assert {item["category"]["id"] for item in found} == set(categories)


def test_warranty_filter_takes_a_range(it_client):
    items = it_client.get("/api/inventory/assets?page_size=200").json()["items"]
    day = next(item["warranty_until"] for item in items if item["warranty_until"])
    found = it_client.get(
        f"/api/inventory/assets?page_size=200&warranty_from={day}&warranty_until={day}"
    ).json()["items"]
    assert found
    assert all(item["warranty_until"] == day for item in found)

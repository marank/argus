"""Live updates: short signals to open browser tabs that something changed.

``publish`` sends a PostgreSQL NOTIFY within the current transaction, so the
signal goes out only on commit, and identical signals of one transaction go out
once. ``apps.core.live_stream`` forwards each signal to the users it is meant
for; the browser then reloads what it shows through the normal API. A signal
carries only a topic and an id, never data. Without PostgreSQL nothing is
published and the stream is unavailable; pages then refresh as before.

Apps declare which model changes are worth a signal with ``track`` (see their
``live.py``), so admin edits and every service path are covered alike.
"""

import json
from collections.abc import Callable, Iterable

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models import Model
from django.db.models.signals import post_delete, post_save

CHANNEL = "argus_live"


def publish(topic: str, id=None, *, users: Iterable = (), staff: bool = True) -> None:
    """Signal a change of ``topic`` (``id``: the changed object) to IT staff and/or ``users`` (ids)."""
    if not settings.LIVE_EVENTS:
        return
    payload = {
        "topic": topic,
        "id": str(id) if id else None,
        # Sorted, so the same change twice in one transaction yields the same payload.
        "users": sorted({str(user) for user in users if user}),
        "staff": staff,
    }
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_notify(%s, %s)", [CHANNEL, json.dumps(payload, separators=(",", ":"))])


def visible_to(event: dict, user_id: str, is_staff: bool) -> bool:
    return (event["staff"] and is_staff) or user_id in event["users"]


Signal = tuple[str, object, Iterable]


def track[M: Model](model: type[M], signal: Callable[[M], Signal | None]) -> None:
    """Publish ``signal(instance)`` (topic, id, users) when an instance of ``model`` is saved or deleted."""

    def changed(sender, instance, **kwargs):
        if not settings.LIVE_EVENTS:
            return
        try:
            result = signal(instance)
        except ObjectDoesNotExist:
            return  # deleted along with its parent, which signals itself
        if result:
            topic, id, users = result
            publish(topic, id, users=users)

    uid = f"live:{model._meta.label}"
    post_save.connect(changed, sender=model, weak=False, dispatch_uid=uid)
    post_delete.connect(changed, sender=model, weak=False, dispatch_uid=uid)

from collections.abc import Callable
from uuid import UUID

from ninja import Schema


class RefOut(Schema):
    """Compact reference to a related record."""

    id: UUID
    name: str


def per_response(context, key: str, load: Callable):
    """For schema resolvers: ``load()``, called once per response rather than once per record."""
    request = (context or {}).get("request")
    if request is None:
        return load()
    cache = request.__dict__.setdefault("_per_response", {})
    if key not in cache:
        cache[key] = load()
    return cache[key]


class MessageOut(Schema):
    detail: str

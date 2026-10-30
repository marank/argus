from collections.abc import Callable
from typing import Any
from uuid import UUID

from ninja import Schema


class RefOut(Schema):
    """Compact reference to a related record."""

    id: UUID
    name: str


def per_response[T](context: dict[str, Any] | None, key: str, load: Callable[[], T]) -> T:
    """For schema resolvers: ``load()``, called once per response rather than once per record."""
    request = (context or {}).get("request")
    if request is None:
        return load()
    # Entries of other keys hold other types; a key is always loaded by the same ``load``.
    cache: dict[str, T] = request.__dict__.setdefault("_per_response", {})
    if key not in cache:
        cache[key] = load()
    return cache[key]


class MessageOut(Schema):
    detail: str

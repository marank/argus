"""The OpenAPI schema names schemas and enums after their classes. A second class of
the same name silently replaces the first, and the frontend's generated types with it,
so names must be unique across the API."""

import enum
import typing
from collections import defaultdict
from collections.abc import Iterable

from ninja import Schema

import config.api  # noqa: F401 - imports every schema module


def subclasses(cls: type[Schema]) -> set[type[Schema]]:
    found: set[type[Schema]] = set()
    for sub in cls.__subclasses__():
        found |= {sub} | subclasses(sub)
    return found


def enums_in(annotation: object) -> set[type[enum.Enum]]:
    if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
        return {annotation}
    found = set()
    for arg in typing.get_args(annotation):
        found |= enums_in(arg)
    return found


def clashes(classes: Iterable[type]) -> dict[str, list[str]]:
    by_name: dict[str, set[type]] = defaultdict(set)
    for cls in classes:
        by_name[cls.__name__].add(cls)
    return {
        name: sorted(f"{cls.__module__}.{cls.__qualname__}" for cls in found)
        for name, found in by_name.items()
        if len(found) > 1
    }


def api_schemas() -> set[type[Schema]]:
    return {schema for schema in subclasses(Schema) if schema.__module__.startswith("apps.")}


def test_schema_names_are_unique():
    assert clashes(api_schemas()) == {}


def test_enum_names_are_unique():
    enums = {
        found
        for schema in api_schemas()
        for field in schema.model_fields.values()
        for found in enums_in(field.annotation)
    }
    assert clashes(enums) == {}


def test_clashes_are_found():
    class Status(enum.Enum):
        OPEN = "open"

    class Other(enum.Enum):
        NEW = "new"

    Other.__name__ = "Status"

    assert enums_in(list[Status | None]) == {Status}
    assert list(clashes([Status, Other])) == ["Status"]

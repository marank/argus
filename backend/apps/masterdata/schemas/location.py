from uuid import UUID

from ninja import Schema

from apps.core.schemas import RefOut


class LocationOut(Schema):
    id: UUID
    name: str
    full_name: str
    code: str
    kind: str
    parent: RefOut | None
    description: str
    is_pickup_point: bool


class LocationIn(Schema):
    name: str
    code: str = ""
    kind: str = "room"
    parent: UUID | None = None
    description: str = ""
    is_pickup_point: bool = False

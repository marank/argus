from uuid import UUID

from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.masterdata.models import LocationKind


class LocationOut(Schema):
    id: UUID
    name: str
    full_name: str
    code: str
    kind: LocationKind
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

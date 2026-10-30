from datetime import datetime
from uuid import UUID

from ninja import Field

from apps.accounts.schemas import UserRefOut
from apps.core.schemas.base import Schema
from apps.inventory.models import ConsumableMovement
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut


class ConsumableOut(Schema):
    id: UUID
    model: AssetModelRefOut
    category: CategoryRefOut = Field(..., alias="model.category")
    location: LocationRefOut
    quantity: int
    reserved_quantity: int
    available_quantity: int
    min_quantity: int
    is_below_minimum: bool


class ConsumableIn(Schema):
    model: UUID
    location: UUID
    min_quantity: int = Field(0, ge=0)


class ConsumableUpdateIn(Schema):
    min_quantity: int = Field(0, ge=0)


class ConsumableMovementOut(Schema):
    id: UUID
    delta: int
    reason: ConsumableMovement.Reason
    note: str
    performed_by: UserRefOut | None
    recipient: UserRefOut | None
    created_at: datetime


class ConsumableMoveIn(Schema):
    delta: int
    reason: ConsumableMovement.Reason
    note: str = ""
    recipient: UUID | None = None

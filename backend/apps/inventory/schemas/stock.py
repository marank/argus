from datetime import datetime
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import UserRefOut
from apps.inventory.models import StockMovement
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut


class StockItemOut(Schema):
    id: UUID
    model: AssetModelRefOut
    category: CategoryRefOut = Field(..., alias="model.category")
    location: LocationRefOut
    quantity: int
    reserved_quantity: int
    available_quantity: int
    min_quantity: int
    is_below_minimum: bool


class StockItemIn(Schema):
    model: UUID
    location: UUID
    min_quantity: int = Field(0, ge=0)


class StockItemUpdateIn(Schema):
    min_quantity: int = Field(0, ge=0)


class StockMovementOut(Schema):
    id: UUID
    delta: int
    reason: str
    note: str
    performed_by: UserRefOut | None
    recipient: UserRefOut | None
    created_at: datetime


class StockMoveIn(Schema):
    delta: int
    reason: StockMovement.Reason
    note: str = ""
    recipient: UUID | None = None

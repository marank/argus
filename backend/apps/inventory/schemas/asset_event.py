from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.utils import timezone
from ninja import Field, Schema

from apps.accounts.schemas import UserRefOut
from apps.inventory.models import AssetEvent

from .refs import AssetRefOut


class ReservationRefOut(Schema):
    id: UUID
    number: str


class AssetEventOut(Schema):
    id: UUID
    kind: str
    occurred_at: datetime
    description: str
    component: str
    component_serial: str
    cost: Decimal | None
    performed_by: UserRefOut | None
    related_user: UserRefOut | None
    reservation: ReservationRefOut | None


class AssetEventWithAssetOut(AssetEventOut):
    asset: AssetRefOut


class ConsumeIn(Schema):
    stock_item_id: UUID
    quantity: int = Field(1, ge=1)


class AssetEventIn(Schema):
    kind: AssetEvent.Kind
    occurred_at: datetime = Field(default_factory=timezone.now)
    description: str = ""
    component: str = ""
    component_serial: str = ""
    cost: Decimal | None = None
    consume: ConsumeIn | None = None

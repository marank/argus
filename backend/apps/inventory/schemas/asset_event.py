from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.utils import timezone
from ninja import Field

from apps.accounts.schemas import UserRefOut
from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.inventory.models import AssetEventKind

from .refs import AssetRefOut


class AssetEventRequestOut(Schema):
    id: UUID
    number: str


class AssetEventOut(Schema):
    id: UUID
    kind: AssetEventKind
    occurred_at: datetime
    description: str
    component: str
    component_serial: str
    component_type: RefOut | None
    previous_serial: str
    cost: Decimal | None
    performed_by: UserRefOut | None
    related_user: UserRefOut | None
    related_asset: AssetRefOut | None
    asset_request: AssetEventRequestOut | None


class AssetEventWithAssetOut(AssetEventOut):
    asset: AssetRefOut


class ConsumeIn(Schema):
    consumable_id: UUID
    quantity: int = Field(1, ge=1)


class AssetEventIn(Schema):
    kind: AssetEventKind
    occurred_at: datetime = Field(default_factory=timezone.now)
    description: str = ""
    component: str = ""
    component_serial: str = ""
    # For "component replaced": the tracked part; the device gets component_serial.
    component_type: UUID | None = None
    cost: Decimal | None = None
    consume: ConsumeIn | None = None

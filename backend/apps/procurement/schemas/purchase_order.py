from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import UserRefOut
from apps.core.schemas import RefOut
from apps.masterdata.schemas.refs import AssetModelRefOut, LocationRefOut
from apps.procurement.models import PurchaseOrder


class ReservationRefOut(Schema):
    id: UUID
    number: str
    requester: UserRefOut


class LineReservationItemOut(Schema):
    id: UUID
    label: str
    reservation: ReservationRefOut


class PurchaseOrderLineOut(Schema):
    id: UUID
    label: str
    asset_model: AssetModelRefOut | None
    description: str
    quantity: int
    quantity_received: int
    quantity_open: int
    unit_price: Decimal | None
    total: Decimal
    reservation_item: LineReservationItemOut | None


class PurchaseOrderListOut(Schema):
    id: UUID
    number: str
    supplier: RefOut | None
    status: str
    order_date: date | None
    expected_date: date | None
    supplier_reference: str
    total: Decimal
    line_count: int = 0
    created_at: datetime

    @staticmethod
    def resolve_line_count(obj) -> int:
        return len(obj.lines.all())


class PurchaseOrderOut(PurchaseOrderListOut):
    delivery_location: LocationRefOut | None
    notes: str
    created_by: UserRefOut | None
    lines: list[PurchaseOrderLineOut]

    @staticmethod
    def resolve_lines(obj):
        return list(obj.lines.all())


class PurchaseOrderLineIn(Schema):
    id: UUID | None = None
    asset_model: UUID | None = None
    description: str = ""
    quantity: int = Field(1, ge=1)
    unit_price: Decimal | None = None
    reservation_item: UUID | None = None


class PurchaseOrderIn(Schema):
    supplier: UUID | None = None
    expected_date: date | None = None
    supplier_reference: str = ""
    delivery_location: UUID | None = None
    notes: str = ""
    lines: list[PurchaseOrderLineIn] | None = None


class MarkOrderedIn(Schema):
    order_date: date | None = None
    expected_date: date | None = None
    supplier_reference: str = ""


class ReceiptIn(Schema):
    line: UUID
    quantity: int = Field(0, ge=0)
    serial_numbers: list[str] = []
    location: UUID | None = None


class ReceiveIn(Schema):
    receipts: list[ReceiptIn] = Field(..., min_length=1)


__all__ = ["PurchaseOrder"]

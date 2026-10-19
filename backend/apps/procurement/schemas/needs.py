from datetime import date
from uuid import UUID

from ninja import Schema

from apps.accounts.schemas import UserRefOut
from apps.core.schemas import RefOut
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut


class NeedReservationOut(Schema):
    id: UUID
    number: str
    title: str
    status: str
    start_date: date
    requester: UserRefOut


class NeedItemOut(Schema):
    id: UUID
    label: str
    is_free_text: bool
    category: CategoryRefOut | None
    asset_model: AssetModelRefOut | None
    default_supplier: RefOut | None = None

    @staticmethod
    def resolve_default_supplier(obj):
        return obj.asset_model.default_supplier if obj.asset_model_id else None


class ReservationNeedOut(Schema):
    reservation_item: NeedItemOut
    reservation: NeedReservationOut
    missing: int
    available: int
    on_order: int
    to_order: int


class ConsumableNeedItemOut(Schema):
    id: UUID
    model: AssetModelRefOut
    location: LocationRefOut
    quantity: int
    min_quantity: int
    default_supplier: RefOut | None = None

    @staticmethod
    def resolve_default_supplier(obj):
        return obj.model.default_supplier


class ConsumableNeedOut(Schema):
    consumable: ConsumableNeedItemOut
    missing: int
    on_order: int
    to_order: int


class NeedsOut(Schema):
    reservations: list[ReservationNeedOut]
    consumables: list[ConsumableNeedOut]

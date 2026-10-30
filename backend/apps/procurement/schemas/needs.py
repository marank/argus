from datetime import date
from uuid import UUID

from ninja import Schema

from apps.accounts.schemas import UserRefOut
from apps.core.schemas import RefOut
from apps.inventory.models import Consumable
from apps.masterdata.models import Supplier
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut
from apps.requests.models import AssetRequestItem, AssetRequestStatus


class NeedAssetRequestOut(Schema):
    id: UUID
    number: str
    title: str
    status: AssetRequestStatus
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
    def resolve_default_supplier(obj: AssetRequestItem) -> Supplier | None:
        return obj.asset_model.default_supplier if obj.asset_model else None


class AssetRequestNeedOut(Schema):
    asset_request_item: NeedItemOut
    asset_request: NeedAssetRequestOut
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
    def resolve_default_supplier(obj: Consumable) -> Supplier | None:
        return obj.model.default_supplier


class ConsumableNeedOut(Schema):
    consumable: ConsumableNeedItemOut
    missing: int
    on_order: int
    to_order: int


class NeedsOut(Schema):
    requests: list[AssetRequestNeedOut]
    consumables: list[ConsumableNeedOut]

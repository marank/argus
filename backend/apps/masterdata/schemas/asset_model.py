from decimal import Decimal
from uuid import UUID

from ninja import Field, Schema

from apps.core.schemas import RefOut
from apps.masterdata.models import AssetModel

from .refs import AssetModelRefOut, CategoryRefOut


class AssetModelOut(Schema):
    id: UUID
    name: str
    full_name: str
    manufacturer: RefOut
    category: CategoryRefOut
    part_number: str
    ean: str
    tracking: str
    description: str
    specifications: str
    default_supplier: RefOut | None
    list_price: Decimal | None
    warranty_months: int
    compatible_with: list[AssetModelRefOut]
    is_requestable: bool
    is_active: bool

    @staticmethod
    def resolve_compatible_with(obj: AssetModel):
        return list(obj.compatible_with.select_related("manufacturer"))


class AssetModelIn(Schema):
    name: str
    manufacturer: UUID
    category: UUID
    part_number: str = ""
    ean: str = ""
    tracking: AssetModel.Tracking = AssetModel.Tracking.SERIALIZED
    description: str = ""
    specifications: str = ""
    default_supplier: UUID | None = None
    list_price: Decimal | None = None
    warranty_months: int = Field(24, ge=0)
    compatible_with: list[UUID] = []
    is_requestable: bool = True
    is_active: bool = True

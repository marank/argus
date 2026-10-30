from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import UserRefOut
from apps.core.schemas import RefOut
from apps.inventory.models import Asset, AssetIssue, LicenseAssignment
from apps.inventory.schemas.asset_issue import OwnIssueOut
from apps.inventory.schemas.license import AssetLicenseOut
from apps.masterdata.models import AssetModel
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut

if TYPE_CHECKING:
    from apps.requests.models import AssetRequest


class AssetOut(Schema):
    id: UUID
    inventory_number: str
    model: AssetModelRefOut
    category: CategoryRefOut = Field(..., alias="model.category")
    manufacturer: RefOut = Field(..., alias="model.manufacturer")
    serial_number: str
    imei: str
    mac_address: str
    hostname: str
    status: str
    condition: str
    is_loanable: bool
    location: LocationRefOut | None
    assigned_to: UserRefOut | None
    assigned_since: datetime | None
    parent: AssetParentOut | None
    supplier: RefOut | None
    purchase_date: date | None
    purchase_price: Decimal | None
    warranty_until: date | None
    notes: str
    created_at: datetime
    updated_at: datetime


class AssetParentOut(Schema):
    id: UUID
    inventory_number: str


class AssetDetailOut(AssetOut):
    components: list[AssetParentOut]
    asset_request: ActiveAssetRequestOut | None = None
    # Assigned to this device directly; ``model_consumables`` come from its model.
    consumables: list[AssetModelRefOut]
    model_consumables: list[AssetModelRefOut]
    licenses: list[AssetLicenseOut]
    open_issues: list[OwnIssueOut]

    @staticmethod
    def resolve_open_issues(obj: Asset) -> list[AssetIssue]:
        return list(obj.issues.exclude(status="resolved"))

    @staticmethod
    def resolve_licenses(obj: Asset) -> list[LicenseAssignment]:
        return list(obj.license_assignments.select_related("license__model__manufacturer"))

    @staticmethod
    def resolve_consumables(obj: Asset) -> list[AssetModel]:
        return list(obj.consumables.select_related("manufacturer"))

    @staticmethod
    def resolve_model_consumables(obj: Asset) -> list[AssetModel]:
        return list(
            obj.model.compatible_with.filter(tracking=AssetModel.Tracking.BULK).select_related("manufacturer")
        )

    @staticmethod
    def resolve_components(obj: Asset) -> list[Asset]:
        return list(obj.components.all())

    @staticmethod
    def resolve_asset_request(obj: Asset) -> AssetRequest | None:
        allocation = (
            obj.asset_request_allocations.filter(returned_at__isnull=True)
            .select_related("item__asset_request__requester")
            .first()
        )
        return allocation.item.asset_request if allocation else None


class ActiveAssetRequestOut(Schema):
    id: UUID
    number: str
    status: str
    requester: UserRefOut


class AssetIn(Schema):
    model: UUID
    inventory_number: str = ""
    serial_number: str = ""
    imei: str = ""
    mac_address: str = ""
    hostname: str = ""
    status: Asset.Status = Asset.Status.IN_STOCK
    condition: Asset.Condition = Asset.Condition.NEW
    is_loanable: bool = True
    location: UUID | None = None
    assigned_to: UUID | None = None
    parent: UUID | None = None
    supplier: UUID | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    warranty_until: date | None = None
    consumables: list[UUID] = []
    notes: str = ""


class AssetBulkIn(Schema):
    model: UUID
    serial_numbers: list[str] = Field(..., min_length=1, max_length=500)
    condition: Asset.Condition = Asset.Condition.NEW
    is_loanable: bool = True
    location: UUID | None = None
    supplier: UUID | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    warranty_until: date | None = None
    notes: str = ""


class AssetSeriesIn(Schema):
    model: UUID
    count: int = Field(..., ge=1, le=500)
    condition: Asset.Condition = Asset.Condition.NEW
    is_loanable: bool = True
    location: UUID | None = None
    supplier: UUID | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    warranty_until: date | None = None
    notes: str = ""


class AssetSeriesPreviewOut(Schema):
    sequence: str
    first: str
    last: str


class AssignIn(Schema):
    user: UUID | None


AssetOut.model_rebuild()
AssetDetailOut.model_rebuild()

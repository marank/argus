from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from ninja import Field

from apps.accounts.schemas import UserRefOut
from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.inventory.models import Asset, AssetComponent, AssetIssue, AssetStatus, LicenseAssignment
from apps.inventory.schemas.asset_issue import OwnIssueOut
from apps.inventory.schemas.license import AssetLicenseOut
from apps.masterdata.models import AssetModel
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut
from apps.requests.models import AssetRequestStatus

if TYPE_CHECKING:
    from apps.requests.models import AssetRequest


class AssetOut(Schema):
    id: UUID
    inventory_number: str
    model: AssetModelRefOut
    category: CategoryRefOut = Field(..., alias="model.category")
    manufacturer: RefOut = Field(..., alias="model.manufacturer")
    serial_number: str
    identifier: str
    imei: str
    mac_address: str
    hostname: str
    status: AssetStatus
    condition: Asset.Condition
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
    # The request a reserved device is set aside for; lists show it where "assigned to" is empty.
    reserved_for: ActiveAssetRequestOut | None = None

    @staticmethod
    def resolve_reserved_for(obj: Asset) -> AssetRequest | None:
        if obj.status != AssetStatus.RESERVED:
            return None
        # Prefetched by the list (asset_queryset); a single device asks the database.
        allocations = getattr(obj, "open_allocations", None)
        if allocations is None:
            allocations = list(
                obj.asset_request_allocations.filter(returned_at__isnull=True).select_related(
                    "item__asset_request__requester"
                )[:1]
            )
        return allocations[0].item.asset_request if allocations else None


class AssetParentOut(Schema):
    id: UUID
    inventory_number: str


class AssetComponentOut(Schema):
    component_type: RefOut
    serial_number: str
    installed_on: date | None


class AssetComponentIn(Schema):
    component_type: UUID
    serial_number: str = ""
    installed_on: date | None = None


class AssetDetailOut(AssetOut):
    components: list[AssetParentOut]
    # The tracked parts fitted now, e.g. the battery (see ComponentType).
    installed_components: list[AssetComponentOut]
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
    def resolve_installed_components(obj: Asset) -> list[AssetComponent]:
        return list(obj.installed_components.select_related("component_type"))

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
    status: AssetRequestStatus
    requester: UserRefOut


class AssetIn(Schema):
    model: UUID
    inventory_number: str = ""
    serial_number: str = ""
    identifier: str = ""
    imei: str = ""
    mac_address: str = ""
    hostname: str = ""
    status: AssetStatus = AssetStatus.IN_STOCK
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
    # None leaves the fitted parts as they are; a list sets them (see services.assets).
    installed_components: list[AssetComponentIn] | None = None
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


class AssetAssignIn(Schema):
    user: UUID | None


AssetOut.model_rebuild()
AssetDetailOut.model_rebuild()

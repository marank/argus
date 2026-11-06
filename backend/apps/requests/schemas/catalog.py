from uuid import UUID

from apps.core.schemas.base import Schema
from apps.inventory.schemas.asset_issue import OwnIssueOut
from apps.masterdata.models import AssetModel, Category, CategoryKind, ModelChoice
from apps.masterdata.schemas.refs import AssetModelRefOut


class CatalogModelOut(Schema):
    id: UUID
    name: str
    full_name: str
    tracking: AssetModel.Tracking
    description: str
    # Only filled for IT staff; employees do not see pool sizes.
    available: int | None
    reserved: int | None
    # Compatible models from accessory categories, for a device (not an accessory itself).
    accessories: list[UUID]


class CatalogCategoryOut(Schema):
    id: UUID
    name: str
    kind: CategoryKind
    item_name: str
    code: str
    icon: str
    description: str
    parent_id: UUID | None
    model_choice: ModelChoice
    # Marked as accessories, here or in a category above.
    holds_accessories: bool
    # Own models only (not subcategories), including requests for "any" device.
    available: int | None
    reserved: int | None
    models: list[CatalogModelOut]

    @staticmethod
    def resolve_holds_accessories(obj: Category) -> bool:
        # Worked out for the whole tree at once by the catalog endpoint.
        return obj.in_accessory_tree


class CountsOut(Schema):
    available: int
    reserved: int


class AvailabilityOut(Schema):
    """Counts in a period, keyed by model and category id."""

    models: dict[str, CountsOut]
    categories: dict[str, CountsOut]


class MenuCountsOut(Schema):
    """Numbers for the self-service menu; ``issues_updated``: IT changed a report since the user looked."""

    requests: int
    approvals: int
    issues: int
    issues_updated: bool


class ConsumableDeviceOut(Schema):
    id: UUID
    inventory_number: str
    model: AssetModelRefOut


class MyConsumablesOut(Schema):
    asset: ConsumableDeviceOut
    consumables: list[AssetModelRefOut]


class MyAssetOut(Schema):
    id: UUID
    inventory_number: str
    serial_number: str
    model: AssetModelRefOut
    category: str
    category_icon: str
    assigned_since: str | None
    asset_request_number: str | None
    return_due: str | None
    issues: list[OwnIssueOut]

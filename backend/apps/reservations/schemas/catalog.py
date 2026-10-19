from uuid import UUID

from ninja import Schema

from apps.inventory.schemas.asset_issue import OwnIssueOut
from apps.masterdata.schemas.refs import AssetModelRefOut


class CatalogModelOut(Schema):
    id: UUID
    name: str
    full_name: str
    tracking: str
    description: str
    # Only filled for IT staff; employees do not see pool sizes.
    available: int | None
    reserved: int | None


class CatalogCategoryOut(Schema):
    id: UUID
    name: str
    kind: str
    item_name: str
    code: str
    icon: str
    description: str
    parent_id: UUID | None
    allow_any_model: bool
    # Own models only (not subcategories), including requests for "any" device.
    available: int | None
    reserved: int | None
    models: list[CatalogModelOut]


class CountsOut(Schema):
    available: int
    reserved: int


class AvailabilityOut(Schema):
    """Counts in a period, keyed by model and category id."""

    models: dict[str, CountsOut]
    categories: dict[str, CountsOut]


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
    reservation_number: str | None
    return_due: str | None
    issues: list[OwnIssueOut]

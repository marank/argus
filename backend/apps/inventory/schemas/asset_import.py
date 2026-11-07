from uuid import UUID

from ninja import Field

from apps.core.schemas.base import Schema
from apps.inventory.models import Asset, AssetStatus
from apps.inventory.services.asset_import import (
    MAX_ROWS,
    ExistingDevices,
    ImportAction,
    ImportField,
    ImportMatch,
)


class AssetImportDefaultsIn(Schema):
    """Values for new devices whose row leaves the field empty."""

    model: UUID | None = None
    location: UUID | None = None
    status: AssetStatus | None = None
    condition: Asset.Condition | None = None


class AssetImportIn(Schema):
    # One entry per row of the file: the text of each mapped column by device field.
    rows: list[dict[ImportField, str]] = Field(..., min_length=1, max_length=MAX_ROWS)
    defaults: AssetImportDefaultsIn = AssetImportDefaultsIn()
    # None: every row creates a new device.
    match_by: ImportMatch | None = ImportMatch.SERIAL_NUMBER
    existing: ExistingDevices = ExistingDevices.UPDATE
    # Recognize "31415a926b" also as "31415A926B".
    ignore_case: bool = False


class AssetImportChangeOut(Schema):
    field: ImportField
    old: str
    new: str


class AssetImportRowOut(Schema):
    row: int
    action: ImportAction
    # The new device in the preview has none yet.
    asset_id: UUID | None
    inventory_number: str
    model: str
    changes: list[AssetImportChangeOut]
    errors: list[str]


class AssetImportResultOut(Schema):
    rows: list[AssetImportRowOut]
    created: int
    updated: int
    unchanged: int
    skipped: int
    failed: int

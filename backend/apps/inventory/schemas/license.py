from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import UserRefOut
from apps.core.schemas import RefOut
from apps.inventory.models import License, LicenseAssignment
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut


class LicenseOut(Schema):
    id: UUID
    model: AssetModelRefOut
    category: CategoryRefOut = Field(..., alias="model.category")
    manufacturer: RefOut = Field(..., alias="model.manufacturer")
    reference: str
    license_key: str
    seats: int
    # Annotated by ``license_queryset``.
    seats_used: int = Field(..., alias="used_seats")
    assign_to: License.AssignTo
    valid_from: date | None
    valid_until: date | None
    is_expired: bool
    supplier: RefOut | None
    purchase_date: date | None
    purchase_price: Decimal | None
    notes: str
    created_at: datetime
    updated_at: datetime


class LicensedAssetOut(Schema):
    id: UUID
    inventory_number: str
    model: AssetModelRefOut
    assigned_to: UserRefOut | None


class LicenseAssignmentOut(Schema):
    id: UUID
    user: UserRefOut | None
    asset: LicensedAssetOut | None
    assigned_by: UserRefOut | None
    note: str
    created_at: datetime


class LicenseDetailOut(LicenseOut):
    assignments: list[LicenseAssignmentOut]

    @staticmethod
    def resolve_assignments(obj: License) -> list[LicenseAssignment]:
        return list(
            obj.assignments.select_related(
                "user", "asset__model__manufacturer", "asset__assigned_to", "assigned_by"
            )
        )


class LicenseIn(Schema):
    model: UUID
    reference: str = ""
    license_key: str = ""
    seats: int = Field(1, ge=1)
    assign_to: License.AssignTo = License.AssignTo.USER
    valid_from: date | None = None
    valid_until: date | None = None
    supplier: UUID | None = None
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    notes: str = ""


class LicenseAssignIn(Schema):
    user: UUID | None = None
    asset: UUID | None = None
    note: str = ""


class OwnLicenseOut(Schema):
    """A license seat the employee uses, directly or through one of their devices. No key."""

    id: UUID
    model: AssetModelRefOut = Field(..., alias="license.model")
    category_icon: str = Field(..., alias="license.model.category.icon")
    valid_until: date | None = Field(..., alias="license.valid_until")
    is_expired: bool = Field(..., alias="license.is_expired")
    assigned_at: datetime = Field(..., alias="created_at")
    # Set when the seat belongs to one of the employee's devices.
    device: LicensedDeviceOut | None = Field(None, alias="asset")


class LicensedDeviceOut(Schema):
    id: UUID
    inventory_number: str
    model: AssetModelRefOut


class AssetLicenseOut(Schema):
    """A license seat used by a device, shown on the device."""

    id: UUID = Field(..., alias="license.id")
    model: AssetModelRefOut = Field(..., alias="license.model")
    reference: str = Field(..., alias="license.reference")
    valid_until: date | None = Field(..., alias="license.valid_until")


OwnLicenseOut.model_rebuild()

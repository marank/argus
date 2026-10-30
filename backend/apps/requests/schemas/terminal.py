from datetime import date, datetime
from uuid import UUID

from ninja import Field, Schema

from apps.core.schemas import RefOut
from apps.inventory.schemas.refs import AssetRefOut
from apps.masterdata.schemas.refs import LocationRefOut
from apps.requests.models import (
    AssetRequest,
    AssetRequestAllocation,
    AssetRequestItem,
    AssetRequestStatus,
    Handover,
    HandoverMethod,
)

from .asset_request import AllocationNoteIn, AllocationOut, ConsumableRefOut, LicenseSeatOut


class TerminalPersonOut(Schema):
    id: UUID
    display_name: str
    employee_number: str
    department: RefOut | None


class TerminalPickupOut(Schema):
    """A prepared pickup as listed on the terminal (no IT-internal details)."""

    id: UUID
    number: str
    title: str
    requester: TerminalPersonOut
    pickup_at: datetime | None
    pickup_location: LocationRefOut | None
    unit_count: int = 0
    summary: str = ""

    @staticmethod
    def resolve_unit_count(obj: AssetRequest) -> int:
        return sum(i.quantity_target for i in obj.items.all())

    @staticmethod
    def resolve_summary(obj: AssetRequest) -> str:
        # Lines IT did not confirm (quantity 0) are nothing to collect.
        return ", ".join(f"{i.quantity_target}× {i.label}" for i in obj.items.all() if i.quantity_target)


class TerminalStaffOut(Schema):
    id: UUID
    display_name: str


class TerminalAllocationOut(Schema):
    """What is handed out, with IT's note for the employee; not who allocated it when."""

    id: UUID
    asset: AssetRefOut | None
    consumable: ConsumableRefOut | None
    license: LicenseSeatOut | None
    quantity: int
    handout_note: str
    category_icon: str

    resolve_license = staticmethod(AllocationOut.resolve_license)
    resolve_category_icon = staticmethod(AllocationOut.resolve_category_icon)


class TerminalPickupItemOut(Schema):
    id: UUID
    label: str
    allocations: list[TerminalAllocationOut]

    @staticmethod
    def resolve_allocations(obj: AssetRequestItem) -> list[AssetRequestAllocation]:
        return list(obj.allocations.all())


class TerminalHandoverOut(Schema):
    method: HandoverMethod
    received_by_name: str
    handed_out_by: TerminalStaffOut | None
    handed_out_at: datetime


class TerminalPickupDetailOut(Schema):
    """A pickup as the terminal shows it while signing.

    The terminal is a shared device, so IT-internal details (notes, comments,
    history, assignment, earlier requests) stay out.
    """

    id: UUID
    number: str
    title: str
    status: AssetRequestStatus
    requester: TerminalStaffOut
    department: RefOut | None = Field(alias="requester.department")
    duration: AssetRequest.Duration
    start_date: date
    end_date: date | None
    pickup_at: datetime | None
    pickup_location: LocationRefOut | None
    skip_device_check: bool
    # Preselects who hands out: whoever prepared the pickup.
    prepared_by: TerminalStaffOut | None
    handled_by: TerminalStaffOut | None
    items: list[TerminalPickupItemOut]
    handover: TerminalHandoverOut | None

    @staticmethod
    def resolve_items(obj: AssetRequest) -> list[AssetRequestItem]:
        return list(obj.items.all())

    @staticmethod
    def resolve_handover(obj: AssetRequest) -> Handover | None:
        return obj.handover if hasattr(obj, "handover") else None


class TerminalSignIn(Schema):
    received_by: UUID | None = Field(None, description="Employee collecting the devices")
    handed_out_by: UUID | None = Field(
        None, description="IT staff member handing out; left out, whoever prepared the pickup"
    )
    received_by_name: str = Field("", max_length=150)
    signature: str = Field(..., description="PNG data URL of the signature")
    notes: str = ""
    allocation_notes: list[AllocationNoteIn] = []

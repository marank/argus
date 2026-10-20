from datetime import date, datetime
from typing import Literal
from uuid import UUID

from ninja import Field, Schema

from apps.accounts.schemas import TeamRefOut, UserRefOut
from apps.core.api.security import context_is_it_staff
from apps.core.schemas import RefOut
from apps.inventory.schemas.refs import AssetRefOut
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut
from apps.reservations.models import Reservation


class ConsumableRefOut(Schema):
    id: UUID
    model: AssetModelRefOut
    location: LocationRefOut


class LicenseSeatOut(Schema):
    """A license seat allocated to a request: the license and the device it is on, if any."""

    id: UUID
    model: AssetModelRefOut
    reference: str
    valid_until: date | None
    device: AssetRefOut | None = None


class AllocationOut(Schema):
    id: UUID
    asset: AssetRefOut | None
    consumable: ConsumableRefOut | None
    license: LicenseSeatOut | None
    quantity: int
    allocated_by: UserRefOut | None
    allocated_at: datetime
    handout_note: str
    handed_out_at: datetime | None
    returned_at: datetime | None
    device_return: UUID | None = Field(None, alias="device_return_id")
    returned_damaged: bool
    return_note: str
    # Icon of the device's category, so lists can show what kind of device it is.
    category_icon: str

    @staticmethod
    def resolve_license(obj):
        if not obj.license_id:
            return None
        assignment = obj.license_assignment
        obj.license.device = assignment.asset if assignment and assignment.asset_id else None
        return obj.license

    @staticmethod
    def resolve_category_icon(obj) -> str:
        return obj.model.category.icon


class ReservationItemOut(Schema):
    id: UUID
    label: str
    category: CategoryRefOut | None
    asset_model: AssetModelRefOut | None
    description: str
    is_free_text: bool
    is_software: bool
    quantity_requested: int
    quantity_confirmed: int | None
    quantity_allocated: int
    quantity_missing: int
    note: str
    allocations: list[AllocationOut]

    @staticmethod
    def resolve_allocations(obj):
        return list(obj.allocations.all())


class ReservationListOut(Schema):
    id: UUID
    number: str
    title: str
    requester: UserRefOut
    department: RefOut | None = Field(None, alias="requester.department")
    duration: str
    start_date: date
    end_date: date | None
    status: str
    handover_mode: str
    is_overdue: bool
    pickup_at: datetime | None
    item_count: int = 0
    unit_count: int = 0
    summary: str = ""
    created_at: datetime
    # IT-internal: always empty for employees (the portal does not show who works on it).
    assigned_team: TeamRefOut | None = None
    assignee: UserRefOut | None = None

    @staticmethod
    def resolve_assigned_team(obj, context):
        return obj.assigned_team if context_is_it_staff(context) else None

    @staticmethod
    def resolve_assignee(obj, context):
        return obj.assignee if context_is_it_staff(context) else None

    @staticmethod
    def resolve_summary(obj) -> str:
        return ", ".join(f"{i.quantity_requested}× {i.label}" for i in obj.items.all())

    @staticmethod
    def resolve_item_count(obj) -> int:
        return len(obj.items.all())

    @staticmethod
    def resolve_unit_count(obj) -> int:
        return sum(i.quantity_target for i in obj.items.all())


class HandoverOut(Schema):
    method: str
    received_by: UserRefOut | None
    received_by_name: str
    signature: str
    notes: str
    location: str
    handed_out_by: UserRefOut | None
    recorded_by: UserRefOut | None
    handed_out_at: datetime


class DeviceReturnOut(Schema):
    id: UUID
    notes: str
    returned_by: UserRefOut | None
    returned_at: datetime


class ReservationOut(ReservationListOut):
    notes: str
    requested_pickup_date: date | None
    skip_device_check: bool
    pickup_location: LocationRefOut | None
    it_comment: str
    created_by: UserRefOut | None
    handled_by: UserRefOut | None
    prepared_by: UserRefOut | None
    reminded_at: datetime | None
    reminded_by: UserRefOut | None
    confirmed_at: datetime | None
    handed_out_at: datetime | None
    completed_at: datetime | None
    items: list[ReservationItemOut]
    handover: HandoverOut | None = None
    returns: list[DeviceReturnOut] = []

    @staticmethod
    def resolve_returns(obj):
        return list(obj.returns.all())

    @staticmethod
    def resolve_items(obj):
        return list(obj.items.all())

    @staticmethod
    def resolve_handover(obj):
        return getattr(obj, "handover", None) if hasattr(obj, "handover") else None


class ReservationItemIn(Schema):
    category: UUID | None = None
    asset_model: UUID | None = None
    description: str = Field("", max_length=255)
    quantity: int = Field(1, ge=1, le=500)
    note: str = ""


class ReservationIn(Schema):
    title: str = Field(..., min_length=1, max_length=200)
    notes: str = ""
    duration: Reservation.Duration = Reservation.Duration.TEMPORARY
    start_date: date
    end_date: date | None = None
    requested_pickup_date: date | None = None
    items: list[ReservationItemIn] = Field(..., min_length=1)
    requester: UUID | None = Field(None, description="IT only: create on behalf of an employee")


class ConfirmItemIn(Schema):
    id: UUID
    quantity_confirmed: int = Field(..., ge=0)


class ConfirmIn(Schema):
    items: list[ConfirmItemIn] = []
    pickup_at: datetime | None = None
    pickup_location: UUID | None = None
    comment: str = ""


class AssignIn(Schema):
    team: UUID | None = None
    assignee: UUID | None = None


class RejectIn(Schema):
    comment: str = Field(..., min_length=1)


class ExtendIn(Schema):
    end_date: date


class ScheduleIn(Schema):
    pickup_at: datetime | None = None
    pickup_location: UUID | None = None
    handover_mode: Reservation.HandoverMode | None = None


class ReadyIn(Schema):
    handover_mode: Reservation.HandoverMode | None = None
    skip_device_check: bool = False
    # Date and place are confirmed with the ready message; left out, they stay as they are.
    pickup_at: datetime | None = None
    pickup_location: UUID | None = None


class AllocationNoteIn(Schema):
    allocation: UUID
    note: str = Field("", max_length=255)


class HandOutIn(Schema):
    """Hand-out documented by IT (no signature): directly or delivered to the employee."""

    method: Literal["direct", "delivered"] = "direct"
    received_by: UUID | None = None
    received_by_name: str = Field("", max_length=150)
    location: str = Field("", max_length=150)
    notes: str = ""
    allocation_notes: list[AllocationNoteIn] = []


class AllocateIn(Schema):
    item: UUID
    asset: UUID | None = Field(None, description="Device to allocate, or the device a license seat is for")
    consumable: UUID | None = None
    license: UUID | None = None
    quantity: int = Field(1, ge=1)
    code: str | None = Field(None, description="Scanned inventory or serial number")


class ResolveItemIn(Schema):
    asset_model: UUID


class ReturnIn(Schema):
    allocations: list[UUID] | None = Field(None, description="Left out: everything still lent")
    notes: str = ""
    allocation_notes: list[AllocationNoteIn] = []
    damaged: list[UUID] = Field([], description="Devices that go to repair instead of back into stock")


class CandidatesOut(Schema):
    assets: list[AssetCandidateOut]
    consumables: list[ConsumableCandidateOut]
    licenses: list[LicenseCandidateOut] = []
    # The requester's devices, for licenses that are assigned to a device.
    devices: list[AssetRefOut] = []


class AssetCandidateOut(Schema):
    id: UUID
    inventory_number: str
    serial_number: str
    condition: str
    model: AssetModelRefOut
    location: LocationRefOut | None


class ConsumableCandidateOut(Schema):
    id: UUID
    model: AssetModelRefOut
    location: LocationRefOut
    available_quantity: int


class LicenseCandidateOut(Schema):
    id: UUID
    model: AssetModelRefOut
    reference: str
    assign_to: str
    valid_until: date | None
    free_seats: int

    @staticmethod
    def resolve_free_seats(obj) -> int:
        return obj.seats - obj.used


CandidatesOut.model_rebuild()

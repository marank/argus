from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict
from uuid import UUID

from ninja import Field

from apps.accounts.models import User
from apps.accounts.schemas import TeamRefOut, UserRefOut
from apps.core.api.security import context_is_it_staff
from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.inventory.models import Asset, License
from apps.inventory.schemas.refs import AssetRefOut
from apps.masterdata.schemas.refs import AssetModelRefOut, CategoryRefOut, LocationRefOut
from apps.requests.models import (
    AssetRequest,
    AssetRequestAllocation,
    AssetRequestEvent,
    AssetRequestEventKind,
    AssetRequestItem,
    AssetRequestStatus,
    DeviceReturn,
    Handover,
    HandoverMethod,
)

if TYPE_CHECKING:
    from django_stubs_ext import WithAnnotations

    from apps.accounts.models import Team


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
    device: AssetRefOut | None


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
    device_return: UUID | None = Field(alias="device_return_id")
    returned_damaged: bool
    return_note: str
    # Icon of the device's category, so lists can show what kind of device it is.
    category_icon: str

    @staticmethod
    def resolve_license(obj: AssetRequestAllocation) -> License | None:
        license = obj.license
        if license is None:
            return None
        assignment = obj.license_assignment
        license.device = assignment.asset if assignment and assignment.asset_id else None
        return license

    @staticmethod
    def resolve_category_icon(obj: AssetRequestAllocation) -> str:
        return obj.model.category.icon


class AssetRequestItemOut(Schema):
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
    def resolve_allocations(obj: AssetRequestItem) -> list[AssetRequestAllocation]:
        return list(obj.allocations.all())


class AssetRequestListOut(Schema):
    id: UUID
    number: str
    title: str
    requester: UserRefOut
    department: RefOut | None = Field(alias="requester.department")
    duration: AssetRequest.Duration
    start_date: date
    end_date: date | None
    status: AssetRequestStatus
    origin: AssetRequest.Origin
    # The department's decision: "" (not needed), pending, approved or rejected.
    approval: AssetRequest.Approval
    handover_mode: AssetRequest.HandoverMode
    is_overdue: bool
    pickup_at: datetime | None
    item_count: int = 0
    unit_count: int = 0
    summary: str = ""
    created_at: datetime
    # IT-internal: always empty for employees (the portal does not show who works on it).
    assigned_team: TeamRefOut | None
    assignee: UserRefOut | None

    @staticmethod
    def resolve_assigned_team(obj: AssetRequest, context: dict[str, Any] | None) -> Team | None:
        return obj.assigned_team if context_is_it_staff(context) else None

    @staticmethod
    def resolve_assignee(obj: AssetRequest, context: dict[str, Any] | None) -> User | None:
        return obj.assignee if context_is_it_staff(context) else None

    @staticmethod
    def resolve_summary(obj: AssetRequest) -> str:
        return ", ".join(f"{i.quantity_requested}× {i.label}" for i in obj.items.all())

    @staticmethod
    def resolve_item_count(obj: AssetRequest) -> int:
        return len(obj.items.all())

    @staticmethod
    def resolve_unit_count(obj: AssetRequest) -> int:
        return sum(i.quantity_target for i in obj.items.all())


class HandoverOut(Schema):
    method: HandoverMethod
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


class FollowsOut(Schema):
    """The earlier request a new one asks again for, with why it ended."""

    id: UUID
    number: str
    status: AssetRequestStatus
    approval: AssetRequest.Approval
    approval_comment: str
    it_comment: str


class AssetRequestEventOut(Schema):
    id: UUID
    kind: AssetRequestEventKind
    at: datetime
    actor: UserRefOut | None
    data: dict[str, Any]


def pending_approvers(asset_request: AssetRequest) -> list[User]:
    """Who may approve while the request waits for approval; asked once per request."""
    if asset_request.status != AssetRequestStatus.PENDING_APPROVAL:
        return []
    if not hasattr(asset_request, "_pending_approvers"):
        asset_request._pending_approvers = list(asset_request.approvers())
    return asset_request._pending_approvers


class AssetRequestOut(AssetRequestListOut):
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
    approver: UserRefOut | None
    approval_decided_at: datetime | None
    approval_comment: str
    # Who can decide while the request awaits approval.
    approvers: list[UserRefOut] = []
    # Whether the current user can approve or decline it now.
    can_approve: bool = False
    confirmed_at: datetime | None
    handed_out_at: datetime | None
    completed_at: datetime | None
    items: list[AssetRequestItemOut]
    handover: HandoverOut | None
    returns: list[DeviceReturnOut] = []
    follows: FollowsOut | None
    # What happened so far: all of it for IT, their part for the employee, and for a
    # department approver only the request and the decision.
    events: list[AssetRequestEventOut] = []

    @staticmethod
    def resolve_events(obj: AssetRequest, context: dict[str, Any] | None) -> list[AssetRequestEvent]:
        events = list(obj.events.all())
        if context_is_it_staff(context):
            return events
        request = (context or {}).get("request")
        kinds: tuple[str, ...]
        if request is not None and request.user.pk == obj.requester_id:
            kinds = AssetRequestEvent.EMPLOYEE_KINDS
        else:
            kinds = AssetRequestEvent.APPROVER_KINDS
        return [e for e in events if e.kind in kinds]

    @staticmethod
    def resolve_approvers(obj: AssetRequest) -> list[User]:
        return pending_approvers(obj)

    @staticmethod
    def resolve_can_approve(obj: AssetRequest, context: dict[str, Any] | None) -> bool:
        request = (context or {}).get("request")
        return request is not None and any(user.pk == request.user.pk for user in pending_approvers(obj))

    @staticmethod
    def resolve_returns(obj: AssetRequest) -> list[DeviceReturn]:
        return list(obj.returns.all())

    @staticmethod
    def resolve_items(obj: AssetRequest) -> list[AssetRequestItem]:
        return list(obj.items.all())

    @staticmethod
    def resolve_handover(obj: AssetRequest) -> Handover | None:
        return obj.handover if hasattr(obj, "handover") else None


class AssetRequestItemIn(Schema):
    category: UUID | None = None
    asset_model: UUID | None = None
    description: str = Field("", max_length=255)
    quantity: int = Field(1, ge=1, le=500)
    note: str = ""


class AssetRequestIn(Schema):
    title: str = Field(..., min_length=1, max_length=200)
    notes: str = ""
    duration: AssetRequest.Duration = AssetRequest.Duration.TEMPORARY
    start_date: date
    end_date: date | None = None
    requested_pickup_date: date | None = None
    items: list[AssetRequestItemIn] = Field(..., min_length=1, max_length=100)
    requester: UUID | None = Field(None, description="IT only: create on behalf of an employee")
    follows: UUID | None = Field(None, description="The earlier request this one asks again for")


class ConfirmItemIn(Schema):
    id: UUID
    quantity_confirmed: int = Field(..., ge=0)


class ConfirmIn(Schema):
    items: list[ConfirmItemIn] = []
    comment: str = ""


class ApproveIn(Schema):
    comment: str = ""


class DeclineIn(Schema):
    comment: str = Field(..., min_length=1)


class AssetRequestAssignIn(Schema):
    team: UUID | None = None
    assignee: UUID | None = None


class RejectIn(Schema):
    comment: str = Field(..., min_length=1)


class ExtendIn(Schema):
    end_date: date


class ScheduleIn(Schema):
    pickup_at: datetime | None = None
    pickup_location: UUID | None = None
    handover_mode: AssetRequest.HandoverMode | None = None
    notify: bool = Field(True, description="Tell the employee, once it was ready")


class ReadyIn(Schema):
    handover_mode: AssetRequest.HandoverMode | None = None
    skip_device_check: bool = False
    # Date and place are confirmed with the ready message; left out, they stay as they are.
    pickup_at: datetime | None = None
    pickup_location: UUID | None = None
    notify: bool = Field(True, description="Send the employee the ready message")


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


class DirectConsumableIn(Schema):
    consumable: UUID
    quantity: int = Field(1, ge=1, le=500)


class DirectRequestIn(Schema):
    """A request with specific devices from stock, picked by IT instead of catalog lines."""

    title: str = Field(..., min_length=1, max_length=200)
    notes: str = ""
    duration: AssetRequest.Duration = AssetRequest.Duration.TEMPORARY
    start_date: date
    end_date: date | None = None
    requested_pickup_date: date | None = None
    requester: UUID | None = Field(None, description="Left out: the current user")
    assets: list[UUID] = []
    consumables: list[DirectConsumableIn] = []


class QuickAssignIn(Schema):
    """A device from stock straight to an employee: no request, no approval."""

    asset: UUID
    requester: UUID
    duration: AssetRequest.Duration = AssetRequest.Duration.TEMPORARY
    start_date: date | None = Field(None, description="Left out: today; earlier: began on that day")
    end_date: date | None = None


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
    condition: Asset.Condition
    model: AssetModelRefOut
    location: LocationRefOut | None


class ConsumableCandidateOut(Schema):
    id: UUID
    model: AssetModelRefOut
    location: LocationRefOut
    available_quantity: int


class UsedSeats(TypedDict):
    used: int


class LicenseCandidateOut(Schema):
    id: UUID
    model: AssetModelRefOut
    reference: str
    assign_to: License.AssignTo
    valid_until: date | None
    free_seats: int

    @staticmethod
    def resolve_free_seats(obj: WithAnnotations[License, UsedSeats]) -> int:
        return obj.seats - obj.used


CandidatesOut.model_rebuild()

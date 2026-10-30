from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from ninja import Field, Query, Router

from apps.accounts.permissions import ResourceKey, can
from apps.accounts.schemas import UserRefOut
from apps.core.api.security import AuthedRequest, it_staff_auth, permission_auth
from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.dashboard.services import widgets
from apps.inventory.models import AssetIssueKind, AssetIssueStatus, Consumable
from apps.inventory.schemas.refs import AssetRefOut
from apps.masterdata.schemas.refs import AssetModelRefOut, LocationRefOut
from apps.procurement.models import PurchaseOrder, PurchaseOrderStatus
from apps.requests.models import AssetRequest, AssetRequestStatus

router = Router(tags=["dashboard"], auth=it_staff_auth)


class TaskRequestOut(Schema):
    id: UUID
    number: str
    title: str
    status: AssetRequestStatus
    start_date: date
    end_date: date | None
    requester: UserRefOut


class TaskIssueOut(Schema):
    id: UUID
    kind: AssetIssueKind
    status: AssetIssueStatus
    description: str
    created_at: datetime
    asset: AssetRefOut
    reported_by: UserRefOut | None


class MyTasksOut(Schema):
    requests: list[TaskRequestOut]
    requests_total: int
    issues: list[TaskIssueOut]
    issues_total: int


class OverdueReturnOut(Schema):
    id: UUID
    number: str
    title: str
    end_date: date
    requester: UserRefOut
    # A reminder needs an email address of an active employee.
    can_remind: bool = Field(..., alias="requester.can_be_reminded")
    reminded_at: datetime | None
    reminded_by: UserRefOut | None


class TeamMemberLoadOut(Schema):
    user: UserRefOut
    requests: int
    issues: int


class TeamLoadOut(Schema):
    people: list[TeamMemberLoadOut]
    unassigned_requests: int
    unassigned_issues: int


class TrendWeekOut(Schema):
    week_start: date
    created: int
    completed: int


@router.get("/my-tasks", response=MyTasksOut)
def my_tasks(request: AuthedRequest) -> widgets.MyTasks:
    return widgets.my_tasks(request.user)


@router.get("/overdue-returns", response=list[OverdueReturnOut], auth=permission_auth(ResourceKey.REQUESTS))
def overdue_returns(request: AuthedRequest) -> list[AssetRequest]:
    return widgets.overdue_returns()


@router.get("/team-load", response=TeamLoadOut)
def team_load(request: AuthedRequest) -> widgets.TeamLoad:
    return widgets.team_load()


@router.get("/request-trend", response=list[TrendWeekOut], auth=permission_auth(ResourceKey.REQUESTS))
def request_trend(request: AuthedRequest) -> list[widgets.TrendWeek]:
    return widgets.request_trend()


class UpcomingOut(Schema):
    id: UUID
    number: str
    title: str
    status: AssetRequestStatus
    start_date: date
    pickup_at: datetime | None
    requester: UserRefOut


class DueReturnOut(OverdueReturnOut):
    pass


class ExpiringOut(Schema):
    kind: Literal["license", "warranty"]
    id: UUID
    label: str
    detail: str
    ends_on: date


class LowStockOut(Schema):
    id: UUID
    model: AssetModelRefOut
    location: LocationRefOut
    quantity: int
    min_quantity: int


class OpenOrderOut(Schema):
    id: UUID
    number: str
    status: PurchaseOrderStatus
    supplier: RefOut | None
    order_date: date | None
    expected_date: date | None


class WaitingRequestOut(Schema):
    id: UUID
    number: str
    title: str
    start_date: date
    created_at: datetime
    requester: UserRefOut
    assignee: UserRefOut | None


# A look-ahead in days; the widgets offer 3, 7 and 14.
Days = Annotated[int, Query(ge=1, le=31)]


@router.get("/upcoming", response=list[UpcomingOut], auth=permission_auth(ResourceKey.REQUESTS))
def upcoming(request: AuthedRequest, days: Days = 7) -> list[AssetRequest]:
    return widgets.upcoming(days)


@router.get("/due-returns", response=list[DueReturnOut], auth=permission_auth(ResourceKey.REQUESTS))
def due_returns(request: AuthedRequest, days: Days = 3) -> list[AssetRequest]:
    return widgets.due_returns(days)


@router.get("/expiring", response=list[ExpiringOut])
def expiring(request: AuthedRequest) -> list[widgets.Expiring]:
    """Only the licenses and devices the user may see."""
    allowed = {
        "license": can(request.user, ResourceKey.LICENSES),
        "warranty": can(request.user, ResourceKey.ASSETS),
    }
    return [row for row in widgets.expiring() if allowed.get(row["kind"], False)]


@router.get("/low-stock", response=list[LowStockOut], auth=permission_auth(ResourceKey.CONSUMABLES))
def low_stock(request: AuthedRequest) -> list[Consumable]:
    return widgets.low_stock()


@router.get("/open-orders", response=list[OpenOrderOut], auth=permission_auth(ResourceKey.PROCUREMENT))
def open_orders(request: AuthedRequest) -> list[PurchaseOrder]:
    return widgets.open_orders()


@router.get("/waiting-requests", response=list[WaitingRequestOut], auth=permission_auth(ResourceKey.REQUESTS))
def waiting_requests(request: AuthedRequest) -> list[AssetRequest]:
    return widgets.waiting_requests()

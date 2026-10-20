from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from django.http import HttpRequest
from ninja import Field, Query, Router, Schema

from apps.accounts.schemas import UserRefOut
from apps.core.api.security import it_staff_auth
from apps.core.schemas import RefOut
from apps.dashboard.services import widgets
from apps.inventory.schemas.refs import AssetRefOut
from apps.masterdata.schemas.refs import AssetModelRefOut, LocationRefOut

router = Router(tags=["dashboard"], auth=it_staff_auth)


class TaskRequestOut(Schema):
    id: UUID
    number: str
    title: str
    status: str
    start_date: date
    end_date: date | None
    requester: UserRefOut


class TaskIssueOut(Schema):
    id: UUID
    kind: str
    status: str
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
def my_tasks(request: HttpRequest):
    return widgets.my_tasks(request.user)


@router.get("/overdue-returns", response=list[OverdueReturnOut])
def overdue_returns(request: HttpRequest):
    return widgets.overdue_returns()


@router.get("/team-load", response=TeamLoadOut)
def team_load(request: HttpRequest):
    return widgets.team_load()


@router.get("/request-trend", response=list[TrendWeekOut])
def request_trend(request: HttpRequest):
    return widgets.request_trend()


class UpcomingOut(Schema):
    id: UUID
    number: str
    title: str
    status: str
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
    status: str
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


@router.get("/upcoming", response=list[UpcomingOut])
def upcoming(request: HttpRequest, days: Days = 7):
    return widgets.upcoming(days)


@router.get("/due-returns", response=list[DueReturnOut])
def due_returns(request: HttpRequest, days: Days = 3):
    return widgets.due_returns(days)


@router.get("/expiring", response=list[ExpiringOut])
def expiring(request: HttpRequest):
    return widgets.expiring()


@router.get("/low-stock", response=list[LowStockOut])
def low_stock(request: HttpRequest):
    return widgets.low_stock()


@router.get("/open-orders", response=list[OpenOrderOut])
def open_orders(request: HttpRequest):
    return widgets.open_orders()


@router.get("/waiting-requests", response=list[WaitingRequestOut])
def waiting_requests(request: HttpRequest):
    return widgets.waiting_requests()

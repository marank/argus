from datetime import date, datetime
from uuid import UUID

from django.http import HttpRequest
from ninja import Field, Router, Schema

from apps.accounts.schemas import UserRefOut
from apps.core.api.security import it_staff_auth
from apps.dashboard.services import widgets
from apps.inventory.schemas.refs import AssetRefOut

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

from datetime import datetime
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Schema

from apps.core.api.security import it_staff_auth
from apps.dashboard.services.overview import employee_overview, it_overview
from apps.inventory.schemas.asset_event import AssetEventWithAssetOut

router = Router(tags=["dashboard"])


class ITOverviewOut(Schema):
    asset_status: dict[str, int]
    reservations_submitted: int
    reservations_to_prepare: int
    reservations_ready: int
    reservations_overdue: int
    orders_to_place: int
    orders_in_transit: int
    low_consumables: int
    open_issues: int
    requests_mine: int
    requests_my_teams: int
    requests_unassigned: int
    issues_mine: int
    warranty_expiring: int
    licenses_expiring: int
    recent_events: list[AssetEventWithAssetOut]


class PickupOut(Schema):
    id: UUID
    number: str
    title: str
    pickup_at: datetime | None


class EmployeeOverviewOut(Schema):
    open_reservations: int
    ready_for_pickup: list[PickupOut]
    assigned_assets: int


@router.get("/it", response=ITOverviewOut, auth=it_staff_auth)
def it(request: HttpRequest):
    return it_overview(request.user)


@router.get("/me", response=EmployeeOverviewOut)
def me(request: HttpRequest):
    return employee_overview(request.user)

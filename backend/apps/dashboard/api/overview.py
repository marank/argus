from datetime import date, datetime
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Schema

from apps.accounts.schemas import UserRefOut
from apps.core.api.security import it_staff_auth
from apps.dashboard.services.overview import employee_overview, it_overview
from apps.inventory.schemas.asset_event import AssetEventWithAssetOut

router = Router(tags=["dashboard"])


class UpcomingOut(Schema):
    id: UUID
    number: str
    title: str
    status: str
    start_date: date
    pickup_at: datetime | None
    requester: UserRefOut


class ITOverviewOut(Schema):
    asset_status: dict[str, int]
    reservations_submitted: int
    reservations_to_prepare: int
    reservations_ready: int
    reservations_overdue: int
    orders_to_place: int
    orders_in_transit: int
    low_consumables: int
    warranty_expiring: int
    upcoming: list[UpcomingOut]
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
    return it_overview()


@router.get("/me", response=EmployeeOverviewOut)
def me(request: HttpRequest):
    return employee_overview(request.user)

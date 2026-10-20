from datetime import datetime
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Schema

from apps.accounts.permissions import can
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


# Figures each area contributes; they stay empty without the right to read the area.
AREA_FIELDS = {
    "assets": {"asset_status": {}, "warranty_expiring": 0, "recent_events": []},
    "reservations": {
        "reservations_submitted": 0,
        "reservations_to_prepare": 0,
        "reservations_ready": 0,
        "reservations_overdue": 0,
        "requests_mine": 0,
        "requests_my_teams": 0,
        "requests_unassigned": 0,
    },
    "procurement": {"orders_to_place": 0, "orders_in_transit": 0},
    "consumables": {"low_consumables": 0},
    "issues": {"open_issues": 0, "issues_mine": 0},
    "licenses": {"licenses_expiring": 0},
}


@router.get("/it", response=ITOverviewOut, auth=it_staff_auth)
def it(request: HttpRequest):
    overview = it_overview(request.user)
    for area, empty in AREA_FIELDS.items():
        if not can(request.user, area):
            overview.update(empty)
    return overview


@router.get("/me", response=EmployeeOverviewOut)
def me(request: HttpRequest):
    return employee_overview(request.user)

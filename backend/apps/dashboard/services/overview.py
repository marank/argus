from datetime import timedelta
from typing import TypedDict

from django.db.models import Count, F, Q, QuerySet
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services.assignment import assigned_q
from apps.core.models import SiteSettings
from apps.inventory.models import (
    Asset,
    AssetEvent,
    AssetIssue,
    AssetIssueStatus,
    AssetStatus,
    Consumable,
    License,
)
from apps.procurement.models import PurchaseOrder, PurchaseOrderStatus
from apps.requests.models import AssetRequest, AssetRequestStatus


def licenses_to_watch() -> QuerySet[License]:
    """Licenses ending within the warning period, and expired ones still assigned to someone."""
    today = timezone.localdate()
    soon = today + timedelta(days=SiteSettings.load().license_warning_days)
    return License.objects.filter(
        Q(valid_until__range=(today, soon)) | Q(valid_until__lt=today, assignments__isnull=False)
    ).distinct()


class ITOverview(TypedDict):
    asset_status: dict[str, int]
    requests_submitted: int
    requests_to_prepare: int
    requests_ready: int
    requests_overdue: int
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
    recent_events: list[AssetEvent]


class ITOverviewPart(TypedDict, total=False):
    """Some of the figures of ``ITOverview``."""

    asset_status: dict[str, int]
    requests_submitted: int
    requests_to_prepare: int
    requests_ready: int
    requests_overdue: int
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
    recent_events: list[AssetEvent]


class EmployeeOverview(TypedDict):
    open_requests: int
    ready_for_pickup: list[AssetRequest]
    assigned_assets: int
    # Lent devices overdue or due back within RETURNS_DUE_DAYS, the earliest first.
    returns_due: list[AssetRequest]


RETURNS_DUE_DAYS = 7


def it_overview(user: User) -> ITOverview:
    today = timezone.localdate()
    rules = SiteSettings.load()
    asset_requests = AssetRequest.objects.all()
    open_requests = asset_requests.filter(status__in=AssetRequest.OPEN_STATUSES)
    open_issues = AssetIssue.objects.exclude(status=AssetIssueStatus.RESOLVED)
    return {
        "asset_status": {
            row["status"]: row["count"] for row in Asset.objects.values("status").annotate(count=Count("id"))
        },
        "requests_submitted": asset_requests.filter(status=AssetRequestStatus.SUBMITTED).count(),
        "requests_to_prepare": asset_requests.filter(status=AssetRequestStatus.CONFIRMED).count(),
        "requests_ready": asset_requests.filter(status=AssetRequestStatus.READY).count(),
        "requests_overdue": asset_requests.filter(
            status=AssetRequestStatus.HANDED_OUT, end_date__lt=today
        ).count(),
        "orders_to_place": PurchaseOrder.objects.filter(status=PurchaseOrderStatus.DRAFT).count(),
        "orders_in_transit": PurchaseOrder.objects.filter(
            status__in=(PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.PARTIALLY_RECEIVED)
        ).count(),
        "low_consumables": Consumable.objects.filter(quantity__lt=F("min_quantity")).count(),
        "open_issues": open_issues.count(),
        # Open requests and reports by who is responsible, for the user's own queue.
        "requests_mine": open_requests.filter(assigned_q(user, "me")).count(),
        "requests_my_teams": open_requests.filter(assigned_q(user, "my_teams")).count(),
        "requests_unassigned": open_requests.filter(assigned_q(user, "nobody")).count(),
        "issues_mine": open_issues.filter(assigned_q(user, "me")).count(),
        "warranty_expiring": Asset.objects.filter(
            warranty_until__range=(today, today + timedelta(days=rules.warranty_warning_days))
        )
        .exclude(status=AssetStatus.RETIRED)
        .count(),
        "licenses_expiring": licenses_to_watch().count(),
        "recent_events": list(
            AssetEvent.objects.select_related("asset__model__manufacturer", "performed_by")[:10]
        ),
    }


def employee_overview(user: User) -> EmployeeOverview:
    mine = AssetRequest.objects.filter(requester=user)
    return {
        "open_requests": mine.filter(status__in=AssetRequest.OPEN_STATUSES).count(),
        "ready_for_pickup": list(mine.filter(status=AssetRequestStatus.READY).order_by("pickup_at")[:5]),
        "assigned_assets": Asset.objects.filter(assigned_to=user).count(),
        "returns_due": list(
            mine.filter(
                status=AssetRequestStatus.HANDED_OUT,
                duration=AssetRequest.Duration.TEMPORARY,
                end_date__lte=timezone.localdate() + timedelta(days=RETURNS_DUE_DAYS),
            ).order_by("end_date", "number")[:5]
        ),
    }

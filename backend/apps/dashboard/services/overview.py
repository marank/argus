from datetime import timedelta

from django.db.models import Count, F
from django.utils import timezone

from apps.accounts.services.assignment import assigned_q
from apps.core.models import SiteSettings
from apps.inventory.models import Asset, AssetEvent, AssetIssue, Consumable, License
from apps.procurement.models import PurchaseOrder
from apps.requests.models import AssetRequest


def it_overview(user) -> dict:
    today = timezone.localdate()
    rules = SiteSettings.load()
    asset_requests = AssetRequest.objects.all()
    open_requests = asset_requests.filter(status__in=AssetRequest.OPEN_STATUSES)
    open_issues = AssetIssue.objects.exclude(status=AssetIssue.Status.RESOLVED)
    return {
        "asset_status": {
            row["status"]: row["count"] for row in Asset.objects.values("status").annotate(count=Count("id"))
        },
        "requests_submitted": asset_requests.filter(status=AssetRequest.Status.SUBMITTED).count(),
        "requests_to_prepare": asset_requests.filter(status=AssetRequest.Status.CONFIRMED).count(),
        "requests_ready": asset_requests.filter(status=AssetRequest.Status.READY).count(),
        "requests_overdue": asset_requests.filter(
            status=AssetRequest.Status.HANDED_OUT, end_date__lt=today
        ).count(),
        "orders_to_place": PurchaseOrder.objects.filter(status=PurchaseOrder.Status.DRAFT).count(),
        "orders_in_transit": PurchaseOrder.objects.filter(
            status__in=(PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED)
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
        .exclude(status=Asset.Status.RETIRED)
        .count(),
        "licenses_expiring": License.objects.filter(
            valid_until__range=(today, today + timedelta(days=rules.license_warning_days))
        ).count(),
        "recent_events": list(
            AssetEvent.objects.select_related("asset__model__manufacturer", "performed_by")[:10]
        ),
    }


def employee_overview(user) -> dict:
    mine = AssetRequest.objects.filter(requester=user)
    return {
        "open_requests": mine.filter(status__in=AssetRequest.OPEN_STATUSES).count(),
        "ready_for_pickup": list(mine.filter(status=AssetRequest.Status.READY).order_by("pickup_at")[:5]),
        "assigned_assets": Asset.objects.filter(assigned_to=user).count(),
    }

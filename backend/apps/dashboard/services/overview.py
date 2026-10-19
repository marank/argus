from datetime import timedelta

from django.db.models import Count, F
from django.utils import timezone

from apps.core.models import SiteSettings
from apps.inventory.models import Asset, AssetEvent, AssetIssue, Consumable, License
from apps.procurement.models import PurchaseOrder
from apps.reservations.models import Reservation


def it_overview() -> dict:
    today = timezone.localdate()
    rules = SiteSettings.load()
    reservations = Reservation.objects.all()
    upcoming = (
        reservations.filter(
            status__in=(Reservation.Status.APPROVED, Reservation.Status.READY),
            start_date__lte=today + timedelta(days=7),
        )
        .select_related("requester")
        .order_by("start_date")[:10]
    )
    return {
        "asset_status": {
            row["status"]: row["count"] for row in Asset.objects.values("status").annotate(count=Count("id"))
        },
        "reservations_submitted": reservations.filter(status=Reservation.Status.SUBMITTED).count(),
        "reservations_to_prepare": reservations.filter(status=Reservation.Status.APPROVED).count(),
        "reservations_ready": reservations.filter(status=Reservation.Status.READY).count(),
        "reservations_overdue": reservations.filter(
            status=Reservation.Status.HANDED_OUT, end_date__lt=today
        ).count(),
        "orders_to_place": PurchaseOrder.objects.filter(status=PurchaseOrder.Status.DRAFT).count(),
        "orders_in_transit": PurchaseOrder.objects.filter(
            status__in=(PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED)
        ).count(),
        "low_consumables": Consumable.objects.filter(quantity__lt=F("min_quantity")).count(),
        "open_issues": AssetIssue.objects.exclude(status=AssetIssue.Status.RESOLVED).count(),
        "warranty_expiring": Asset.objects.filter(
            warranty_until__range=(today, today + timedelta(days=rules.warranty_warning_days))
        )
        .exclude(status=Asset.Status.RETIRED)
        .count(),
        "licenses_expiring": License.objects.filter(
            valid_until__range=(today, today + timedelta(days=rules.license_warning_days))
        ).count(),
        "upcoming": list(upcoming),
        "recent_events": list(
            AssetEvent.objects.select_related("asset__model__manufacturer", "performed_by")[:10]
        ),
    }


def employee_overview(user) -> dict:
    mine = Reservation.objects.filter(requester=user)
    return {
        "open_reservations": mine.filter(status__in=Reservation.OPEN_STATUSES).count(),
        "ready_for_pickup": list(mine.filter(status=Reservation.Status.READY).order_by("pickup_at")[:5]),
        "assigned_assets": Asset.objects.filter(assigned_to=user).count(),
    }

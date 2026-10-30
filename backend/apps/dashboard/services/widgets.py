"""Data of the optional dashboard widgets; each is fetched only while it is on the dashboard."""

from datetime import date, timedelta
from typing import Literal, TypedDict
from uuid import UUID

from django.db.models import Count, DateField, F, QuerySet
from django.db.models.functions import TruncWeek
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services.assignment import assigned_q
from apps.core.models import SiteSettings
from apps.core.notifications import it_staff
from apps.inventory.models import Asset, AssetIssue, Consumable, License
from apps.procurement.models import PurchaseOrder
from apps.requests.models import AssetRequest

LIST_LIMIT = 10


class MyTasks(TypedDict):
    requests: list[AssetRequest]
    requests_total: int
    issues: list[AssetIssue]
    issues_total: int


class TeamMemberLoad(TypedDict):
    user: User
    requests: int
    issues: int


class TeamLoad(TypedDict):
    people: list[TeamMemberLoad]
    unassigned_requests: int
    unassigned_issues: int


class TrendWeek(TypedDict):
    week_start: date
    created: int
    completed: int


class Expiring(TypedDict):
    kind: Literal["license", "warranty"]
    id: UUID
    label: str
    detail: str
    ends_on: date


def open_issues() -> QuerySet[AssetIssue]:
    return AssetIssue.objects.exclude(status=AssetIssue.Status.RESOLVED)


def my_tasks(user: User) -> MyTasks:
    """Open requests and problem reports assigned to the user personally, oldest first."""
    requests = (
        AssetRequest.objects.filter(status__in=AssetRequest.OPEN_STATUSES)
        .filter(assigned_q(user, "me"))
        .select_related("requester")
        .order_by("start_date", "number")
    )
    issues = (
        open_issues()
        .filter(assigned_q(user, "me"))
        .select_related("asset__model__manufacturer", "reported_by")
        .order_by("created_at")
    )
    return {
        "requests": list(requests[:LIST_LIMIT]),
        "requests_total": requests.count(),
        "issues": list(issues[:LIST_LIMIT]),
        "issues_total": issues.count(),
    }


def overdue_returns() -> list[AssetRequest]:
    """Lent devices whose return date has passed, the longest overdue first."""
    return list(
        AssetRequest.objects.filter(
            status=AssetRequest.Status.HANDED_OUT,
            duration=AssetRequest.Duration.TEMPORARY,
            end_date__lt=timezone.localdate(),
        )
        .select_related("requester", "reminded_by")
        .order_by("end_date", "number")[:20]
    )


def team_load() -> TeamLoad:
    """Open requests and problem reports per IT member, and those nobody has taken yet."""
    open_requests = AssetRequest.objects.filter(status__in=AssetRequest.OPEN_STATUSES)
    requests = dict(
        open_requests.exclude(assignee=None).values_list("assignee").annotate(n=Count("id")).order_by()
    )
    issues = dict(
        open_issues().exclude(assignee=None).values_list("assignee").annotate(n=Count("id")).order_by()
    )
    people: list[TeamMemberLoad] = [
        {"user": person, "requests": requests.get(person.pk, 0), "issues": issues.get(person.pk, 0)}
        for person in it_staff()
    ]
    people.sort(key=lambda row: (-(row["requests"] + row["issues"]), row["user"].display_name))
    return {
        "people": people,
        "unassigned_requests": open_requests.filter(assignee=None).count(),
        "unassigned_issues": open_issues().filter(assignee=None).count(),
    }


def request_trend(weeks: int = 12) -> list[TrendWeek]:
    """New and completed requests per calendar week (Monday), the current week last."""
    today = timezone.localdate()
    first = today - timedelta(days=today.weekday() + 7 * (weeks - 1))

    def per_week(field: str) -> dict[date, int]:
        return dict(
            AssetRequest.objects.filter(**{f"{field}__date__gte": first})
            .annotate(week=TruncWeek(field, output_field=DateField()))
            .values_list("week")
            .annotate(n=Count("id"))
            .order_by()
        )

    created, completed = per_week("created_at"), per_week("completed_at")
    return [
        {"week_start": start, "created": created.get(start, 0), "completed": completed.get(start, 0)}
        for start in (first + timedelta(weeks=i) for i in range(weeks))
    ]


def upcoming(days: int) -> list[AssetRequest]:
    """Confirmed and prepared requests to hand out within `days` days, the earliest first."""
    return list(
        AssetRequest.objects.filter(
            status__in=(AssetRequest.Status.CONFIRMED, AssetRequest.Status.READY),
            start_date__lte=timezone.localdate() + timedelta(days=days),
        )
        .select_related("requester")
        .order_by("start_date", "pickup_at", "number")[:20]
    )


def due_returns(days: int) -> list[AssetRequest]:
    """Lent devices due back within `days` days (not yet overdue), the soonest first."""
    today = timezone.localdate()
    return list(
        AssetRequest.objects.filter(
            status=AssetRequest.Status.HANDED_OUT,
            duration=AssetRequest.Duration.TEMPORARY,
            end_date__range=(today, today + timedelta(days=days)),
        )
        .select_related("requester", "reminded_by")
        .order_by("end_date", "number")[:20]
    )


def expiring() -> list[Expiring]:
    """Licenses and warranties ending within the warning periods of the site rules, the soonest first."""
    today = timezone.localdate()
    rules = SiteSettings.load()
    licenses = License.objects.filter(
        valid_until__range=(today, today + timedelta(days=rules.license_warning_days))
    ).select_related("model__manufacturer")
    assets = (
        Asset.objects.filter(
            warranty_until__range=(today, today + timedelta(days=rules.warranty_warning_days))
        )
        .exclude(status=Asset.Status.RETIRED)
        .select_related("model__manufacturer")
    )
    rows: list[Expiring] = []
    for lic in licenses:
        assert lic.valid_until is not None  # the filter excludes NULL
        rows.append(
            {"kind": "license", "id": lic.pk, "label": str(lic), "detail": "", "ends_on": lic.valid_until}
        )
    for asset in assets:
        assert asset.warranty_until is not None  # the filter excludes NULL
        rows.append(
            {
                "kind": "warranty",
                "id": asset.pk,
                "label": asset.inventory_number,
                "detail": asset.model.full_name,
                "ends_on": asset.warranty_until,
            }
        )
    return sorted(rows, key=lambda row: (row["ends_on"], row["label"]))[:20]


def low_stock() -> list[Consumable]:
    """Consumables below their minimum, the largest shortfall first."""
    return list(
        Consumable.objects.filter(quantity__lt=F("min_quantity"))
        .select_related("model__manufacturer", "location")
        .order_by(F("quantity") - F("min_quantity"), "model__name")[:20]
    )


def open_orders() -> list[PurchaseOrder]:
    """Placed orders not fully received, the earliest expected delivery first (undated last)."""
    return list(
        PurchaseOrder.objects.filter(
            status__in=(PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED)
        )
        .select_related("supplier")
        .order_by(F("expected_date").asc(nulls_last=True), "number")[:20]
    )


def waiting_requests() -> list[AssetRequest]:
    """Submitted requests waiting for IT to confirm them, the longest waiting first."""
    return list(
        AssetRequest.objects.filter(status=AssetRequest.Status.SUBMITTED)
        .select_related("requester", "assignee")
        .order_by("created_at")[:20]
    )

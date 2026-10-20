"""Data of the optional dashboard widgets; each is fetched only while it is on the dashboard."""

from datetime import timedelta

from django.db.models import Count, DateField
from django.db.models.functions import TruncWeek
from django.utils import timezone

from apps.accounts.services.assignment import assigned_q
from apps.core.notifications import it_staff
from apps.inventory.models import AssetIssue
from apps.reservations.models import Reservation

LIST_LIMIT = 10


def open_issues():
    return AssetIssue.objects.exclude(status=AssetIssue.Status.RESOLVED)


def my_tasks(user) -> dict:
    """Open requests and problem reports assigned to the user personally, oldest first."""
    requests = (
        Reservation.objects.filter(status__in=Reservation.OPEN_STATUSES)
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


def overdue_returns() -> list[Reservation]:
    """Lent devices whose return date has passed, the longest overdue first."""
    return list(
        Reservation.objects.filter(
            status=Reservation.Status.HANDED_OUT,
            duration=Reservation.Duration.TEMPORARY,
            end_date__lt=timezone.localdate(),
        )
        .select_related("requester", "reminded_by")
        .order_by("end_date", "number")[:20]
    )


def team_load() -> dict:
    """Open requests and problem reports per IT member, and those nobody has taken yet."""
    open_requests = Reservation.objects.filter(status__in=Reservation.OPEN_STATUSES)
    requests = dict(
        open_requests.exclude(assignee=None).values_list("assignee").annotate(n=Count("id")).order_by()
    )
    issues = dict(
        open_issues().exclude(assignee=None).values_list("assignee").annotate(n=Count("id")).order_by()
    )
    people = [
        {"user": person, "requests": requests.get(person.pk, 0), "issues": issues.get(person.pk, 0)}
        for person in it_staff()
    ]
    people.sort(key=lambda row: (-(row["requests"] + row["issues"]), row["user"].display_name))
    return {
        "people": people,
        "unassigned_requests": open_requests.filter(assignee=None).count(),
        "unassigned_issues": open_issues().filter(assignee=None).count(),
    }


def request_trend(weeks: int = 12) -> list[dict]:
    """New and completed requests per calendar week (Monday), the current week last."""
    today = timezone.localdate()
    first = today - timedelta(days=today.weekday() + 7 * (weeks - 1))

    def per_week(field: str) -> dict:
        return dict(
            Reservation.objects.filter(**{f"{field}__date__gte": first})
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

"""Delegations of approvers: who decides on approvals in their place, and when."""

from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import ApprovalDelegation, User


def deciders(approvers: QuerySet[User]) -> QuerySet[User]:
    """The approvers plus their delegates whose delegation runs today (active accounts only)."""
    delegations = ApprovalDelegation.objects.running().filter(approver__in=approvers).values("delegate")
    return User.objects.filter(Q(pk__in=approvers.values("pk")) | Q(pk__in=delegations), is_active=True)


def represented(user: User) -> QuerySet[User]:
    """Active approvers that ``user`` decides for today as their delegate."""
    approvers = ApprovalDelegation.objects.running().filter(delegate=user).values("approver")
    named = User.objects.filter(pk__in=approvers, is_active=True, approving_departments__isnull=False)
    return named.distinct()


def current_and_future(approver: User) -> QuerySet[ApprovalDelegation]:
    """The approver's delegations that have not ended yet."""
    today = timezone.localdate()
    return (
        approver.delegations.filter(Q(ends_on__isnull=True) | Q(ends_on__gte=today))
        .select_related("delegate")
        .order_by("starts_on", "created_at")
    )


def add(approver: User, delegate: User, starts_on: date, ends_on: date | None) -> ApprovalDelegation:
    if not approver.approving_departments.exists():
        raise ValidationError(_("Only approvers of a department can delegate approvals."))
    if not delegate.is_active or delegate.is_terminal:
        raise ValidationError(_("Choose an active employee as delegate."))
    if starts_on < timezone.localdate():
        raise ValidationError(_("The start must not be in the past."))
    entry = ApprovalDelegation(approver=approver, delegate=delegate, starts_on=starts_on, ends_on=ends_on)
    entry.full_clean()
    entry.save()
    return entry


def past(approver: User, limit: int = 10) -> QuerySet[ApprovalDelegation]:
    """The approver's last delegations whose period is over, the most recent first."""
    return (
        approver.delegations.filter(ends_on__lt=timezone.localdate())
        .select_related("delegate", "approver")
        .order_by("-ends_on", "-starts_on")[:limit]
    )


def status(entry: ApprovalDelegation) -> str:
    today = timezone.localdate()
    if entry.ends_on is not None and entry.ends_on < today:
        return "ended"
    return "planned" if entry.starts_on > today else "running"


def change_period(entry: ApprovalDelegation, starts_on: date, ends_on: date | None) -> ApprovalDelegation:
    """A new period; once started, the start stays, and the end must not be in the past."""
    today = timezone.localdate()
    if status(entry) == "ended":
        raise ValidationError(_("This delegation is over."))
    if entry.starts_on <= today:
        if starts_on != entry.starts_on:
            raise ValidationError(_("The delegation has started; only the end can change."))
    elif starts_on < today:
        raise ValidationError(_("The start must not be in the past."))
    if ends_on is not None and ends_on < today:
        raise ValidationError(_("The end must not be in the past."))
    entry.starts_on, entry.ends_on = starts_on, ends_on
    entry.full_clean()
    entry.save(update_fields=["starts_on", "ends_on", "updated_at"])
    return entry


def end_now(entry: ApprovalDelegation) -> ApprovalDelegation | None:
    """Ends a running delegation today (kept as history from yesterday), or drops a planned one.

    Returns the kept entry, or None when it was removed.
    """
    today = timezone.localdate()
    if status(entry) != "running" or entry.starts_on >= today:
        entry.delete()
        return None
    entry.ends_on = today - timedelta(days=1)
    entry.save(update_fields=["ends_on", "updated_at"])
    return entry

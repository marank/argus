from typing import Any

from django.db import transaction
from django.db.models import Prefetch, QuerySet
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.accounts.services import assignment
from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, AssetEvent, AssetIssue, AssetIssueEntry
from apps.inventory.services import notifications
from apps.inventory.services.events import log_event

Status = AssetIssue.Status


@transaction.atomic
def report_issue(asset: Asset, user: User, kind: str, description: str) -> AssetIssue:
    """An employee reports a problem with a device handed out to them."""
    description = description.strip()
    if not description:
        raise BusinessError(_("Describe the problem."))
    issue = AssetIssue.objects.create(
        asset=asset,
        kind=kind,
        description=description,
        reported_by=user,
        assigned_team=assignment.route([asset.model.effective_team()]),
    )
    log_event(
        asset,
        AssetEvent.Kind.ISSUE_REPORTED,
        user,
        related_user=user,
        description=f"{issue.get_kind_display()}: {description}",
    )
    notifications.issue_reported(issue)
    return issue


def _is_reporter(issue: AssetIssue, user: User) -> bool:
    return bool(issue.reported_by_id == user.pk)


def _add_entry(issue: AssetIssue, user: User, **fields: Any) -> AssetIssueEntry:
    """Record a step; what IT does is news for the reporter until they look."""
    if not _is_reporter(issue, user) and not issue.unseen_update:
        issue.unseen_update = True
        issue.save(update_fields=["unseen_update", "updated_at"])
    return AssetIssueEntry.objects.create(issue=issue, author=user, **fields)


@transaction.atomic
def post_message(issue: AssetIssue, user: User, text: str, *, by_it: bool) -> AssetIssueEntry:
    """Reporter (``by_it`` false) or IT write to the other side, whatever the status."""
    text = text.strip()
    if not text:
        raise BusinessError(_("Write a message."))
    entry = _add_entry(issue, user, kind=AssetIssueEntry.Kind.MESSAGE, text=text)
    if by_it:
        notifications.issue_message(issue, text)
    else:
        notifications.issue_answered(issue, text)
    return entry


@transaction.atomic
def update_issue(issue: AssetIssue, user: User, status: str, message: str = "", *, by_it: bool) -> AssetIssue:
    """Change the status, with an optional message sent along.

    IT may set any status; the reporter (``by_it`` false) may only mark the problem resolved.
    """
    if not by_it and status != Status.RESOLVED:
        raise BusinessError(_("Only IT can take a report into work or reopen it."))
    if status == issue.status:
        raise BusinessError(_("The report already has this status."))
    message = message.strip()
    if message:
        _add_entry(issue, user, kind=AssetIssueEntry.Kind.MESSAGE, text=message)
    issue.status = status
    if by_it:
        issue.handled_by = user
    issue.resolved_at = timezone.now() if status == Status.RESOLVED else None
    issue.save()
    _add_entry(issue, user, kind=AssetIssueEntry.Kind.STATUS, status=status)
    if status == Status.RESOLVED:
        log_event(
            issue.asset,
            AssetEvent.Kind.ISSUE_RESOLVED,
            user,
            related_user=issue.reported_by,
            description=message,
        )
    if not by_it:
        notifications.issue_answered(issue, message, resolved=True)
    elif status == Status.RESOLVED:
        notifications.issue_resolved(issue, message)
    elif message:
        notifications.issue_message(issue, message)
    return issue


def mark_seen(user: User, issue: AssetIssue) -> None:
    """The reporter opened the report: IT's updates are no longer news."""
    AssetIssue.objects.filter(pk=issue.pk, reported_by=user, unseen_update=True).update(unseen_update=False)


def with_messages(issues: QuerySet[AssetIssue]) -> QuerySet[AssetIssue]:
    """Loads the messages of all reports at once, for ``OwnIssueOut.last_message``."""
    messages = AssetIssueEntry.objects.filter(kind=AssetIssueEntry.Kind.MESSAGE).order_by("created_at")
    return issues.prefetch_related(Prefetch("entries", queryset=messages, to_attr="messages"))

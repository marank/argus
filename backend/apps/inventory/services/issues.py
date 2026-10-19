from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, AssetEvent, AssetIssue
from apps.inventory.services.events import log_event

Status = AssetIssue.Status


@transaction.atomic
def report_issue(asset: Asset, user, kind: str, description: str) -> AssetIssue:
    """An employee reports a problem with a device handed out to them."""
    description = description.strip()
    if not description:
        raise BusinessError(_("Describe the problem."))
    issue = AssetIssue.objects.create(asset=asset, kind=kind, description=description, reported_by=user)
    log_event(
        asset,
        AssetEvent.Kind.ISSUE_REPORTED,
        user,
        related_user=user,
        description=f"{issue.get_kind_display()}: {description}",
    )
    return issue


@transaction.atomic
def update_issue(issue: AssetIssue, user, status: str, resolution: str = "") -> AssetIssue:
    """IT takes a report into work or resolves it; resolving needs a note for the employee."""
    resolution = resolution.strip()
    if status == Status.RESOLVED and not resolution:
        raise BusinessError(_("Describe how the problem was solved."))
    was_resolved = issue.status == Status.RESOLVED
    issue.status = status
    issue.handled_by = user
    if status == Status.RESOLVED:
        issue.resolution = resolution
        issue.resolved_at = timezone.now()
    else:
        issue.resolved_at = None
    issue.save()
    if status == Status.RESOLVED and not was_resolved:
        log_event(
            issue.asset,
            AssetEvent.Kind.ISSUE_RESOLVED,
            user,
            related_user=issue.reported_by,
            description=resolution,
        )
    return issue

"""Email notifications about problem reports and licenses."""

from django.utils import formats
from django.utils.translation import gettext as _

from apps.accounts.services.assignment import responsible_staff
from apps.core.notifications import it_staff, notify
from apps.inventory.models import AssetIssue, License


def issue_reported(issue: AssetIssue) -> None:
    def render(user: object) -> tuple[str, str]:
        subject = _("Problem reported: %(device)s") % {"device": issue.asset.inventory_number}
        body = _("%(name)s reports for %(device)s (%(model)s): %(kind)s") % {
            "name": issue.reported_by.display_name if issue.reported_by else "—",
            "device": issue.asset.inventory_number,
            "model": issue.asset.model.full_name,
            "kind": issue.get_kind_display(),
        }
        return subject, f"{body}\n\n{issue.description}"

    notify("issue_reported", responsible_staff(issue), render, path=_it_path(issue))


def issue_assigned(issue: AssetIssue) -> None:
    assignee = issue.assignee
    if assignee is None:
        return

    def render(user: object) -> tuple[str, str]:
        subject = _("Assigned to you: problem report for %(device)s") % {
            "device": issue.asset.inventory_number
        }
        body = _("You are now responsible for this report on %(device)s (%(model)s): %(kind)s") % {
            "device": issue.asset.inventory_number,
            "model": issue.asset.model.full_name,
            "kind": issue.get_kind_display(),
        }
        return subject, f"{body}\n\n{issue.description}"

    notify("assigned_to_me", [assignee], render, path=_it_path(issue))


def _it_path(issue: AssetIssue) -> str:
    return f"/inventory/issues/{issue.pk}"


def _reporter_path(issue: AssetIssue) -> str:
    return f"/portal/issues/{issue.pk}"


def issue_resolved(issue: AssetIssue, message: str) -> None:
    if not issue.reported_by:
        return

    def render(user: object) -> tuple[str, str]:
        subject = _("Your problem report for %(device)s was resolved") % {
            "device": issue.asset.inventory_number
        }
        body = _("IT resolved your report “%(description)s”.") % {"description": issue.description}
        if message:
            # Outside the f-string, where makemessages finds it.
            label = _("Message from IT:")
            body = f"{body}\n\n{label} {message}"
        return subject, body

    notify("issue_resolved", [issue.reported_by], render, path=_reporter_path(issue))


def issue_message(issue: AssetIssue, message: str) -> None:
    """IT wrote to the reporter."""
    if not issue.reported_by:
        return

    def render(user: object) -> tuple[str, str]:
        subject = _("Message on your problem report for %(device)s") % {
            "device": issue.asset.inventory_number
        }
        body = _("IT wrote about your report “%(description)s”:") % {"description": issue.description}
        return subject, f"{body}\n\n{message}"

    notify("issue_message", [issue.reported_by], render, path=_reporter_path(issue))


def issue_answered(issue: AssetIssue, message: str, *, resolved: bool = False) -> None:
    """The reporter wrote to IT or marked the problem resolved themselves."""
    name = issue.reported_by.display_name if issue.reported_by else "—"

    def render(user: object) -> tuple[str, str]:
        values = {"name": name, "device": issue.asset.inventory_number}
        if resolved:
            subject = _("Resolved by the reporter: %(device)s") % values
            body = _("%(name)s marked the report on %(device)s as resolved.") % values
        else:
            subject = _("Answer on problem report: %(device)s") % values
            body = _("%(name)s wrote about the report on %(device)s:") % values
        return subject, f"{body}\n\n{message}" if message else body

    recipients = [u for u in responsible_staff(issue) if u.pk != issue.reported_by_id]
    notify("issue_answered", recipients, render, path=_it_path(issue))


def license_expiring(license: License) -> None:
    valid_until = license.valid_until
    assert valid_until is not None  # only licenses that end are reminded of

    def render(user: object) -> tuple[str, str]:
        subject = _("License ends on %(date)s: %(name)s") % {
            "date": formats.date_format(valid_until, "SHORT_DATE_FORMAT"),
            "name": license.model.full_name,
        }
        body = _("The license %(name)s %(reference)s ends on %(date)s.") % {
            "name": license.model.full_name,
            "reference": f"({license.reference})" if license.reference else "",
            "date": formats.date_format(valid_until, "SHORT_DATE_FORMAT"),
        }
        return subject, body

    notify(
        "license_expiring",
        it_staff(),
        render,
        key=f"{license.pk}:{license.valid_until}",
        path=f"/inventory/licenses/{license.pk}",
    )

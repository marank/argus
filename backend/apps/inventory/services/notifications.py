"""Email notifications about problem reports and licenses."""

from django.utils import formats
from django.utils.translation import gettext as _

from apps.core.notifications import it_staff, notify
from apps.inventory.models import AssetIssue, License


def issue_reported(issue: AssetIssue) -> None:
    def render(user):
        subject = _("Problem reported: %(device)s") % {"device": issue.asset.inventory_number}
        body = _("%(name)s reports for %(device)s (%(model)s): %(kind)s") % {
            "name": issue.reported_by.display_name if issue.reported_by else "—",
            "device": issue.asset.inventory_number,
            "model": issue.asset.model.full_name,
            "kind": issue.get_kind_display(),
        }
        return subject, f"{body}\n\n{issue.description}"

    notify("issue_reported", it_staff(), render, path="/inventory/issues")


def issue_resolved(issue: AssetIssue) -> None:
    if not issue.reported_by:
        return

    def render(user):
        subject = _("Your problem report for %(device)s was resolved") % {
            "device": issue.asset.inventory_number
        }
        body = _("IT resolved your report “%(description)s”.") % {"description": issue.description}
        return subject, f"{body}\n\n{_('Answer from IT:')} {issue.resolution}"

    notify("issue_resolved", [issue.reported_by], render, path=f"/portal/devices/{issue.asset_id}")


def license_expiring(license: License) -> None:
    def render(user):
        subject = _("License ends on %(date)s: %(name)s") % {
            "date": formats.date_format(license.valid_until, "SHORT_DATE_FORMAT"),
            "name": license.model.full_name,
        }
        body = _("The license %(name)s %(reference)s ends on %(date)s.") % {
            "name": license.model.full_name,
            "reference": f"({license.reference})" if license.reference else "",
            "date": formats.date_format(license.valid_until, "SHORT_DATE_FORMAT"),
        }
        return subject, body

    notify(
        "license_expiring",
        it_staff(),
        render,
        key=f"{license.pk}:{license.valid_until}",
        path=f"/inventory/licenses/{license.pk}",
    )

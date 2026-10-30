"""Email notifications about requests (texts rendered in the recipient's language)."""

from datetime import date
from typing import TYPE_CHECKING

from django.utils import formats, timezone
from django.utils.translation import gettext as _

from apps.accounts.services.assignment import responsible_staff
from apps.core.notifications import notify
from apps.requests.models import AssetRequest, AssetRequestStatus

if TYPE_CHECKING:
    from apps.accounts.models import User


def _items(asset_request: AssetRequest) -> str:
    return "\n".join(f"- {item.quantity_target} × {item.label}" for item in asset_request.items.all())


def _date(value: date | None) -> str:
    return formats.date_format(value, "SHORT_DATE_FORMAT") if value else "—"


def _pickup(asset_request: AssetRequest) -> str:
    if not asset_request.pickup_at:
        return ""
    when = formats.date_format(timezone.localtime(asset_request.pickup_at), "SHORT_DATETIME_FORMAT")
    place = f", {asset_request.pickup_location.full_name}" if asset_request.pickup_location else ""
    return _("Pickup: %(when)s%(place)s") % {"when": when, "place": place}


def request_submitted(asset_request: AssetRequest) -> None:
    def render(user: object) -> tuple[str, str]:
        subject = _("New request %(number)s from %(name)s") % {
            "number": asset_request.number,
            "name": asset_request.requester.display_name,
        }
        body = _("%(name)s requests for “%(title)s”:") % {
            "name": asset_request.requester.display_name,
            "title": asset_request.title,
        }
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify(
        "request_submitted",
        responsible_staff(asset_request).exclude(pk=asset_request.requester_id),
        render,
        path=f"/requests/{asset_request.pk}",
    )


def approval_requested(asset_request: AssetRequest) -> None:
    def render(user: object) -> tuple[str, str]:
        subject = _("Approval needed: request %(number)s from %(name)s") % {
            "number": asset_request.number,
            "name": asset_request.requester.display_name,
        }
        body = _("%(name)s requests for “%(title)s” and needs your approval:") % {
            "name": asset_request.requester.display_name,
            "title": asset_request.title,
        }
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify(
        "approval_requested",
        asset_request.approvers().exclude(pk=asset_request.requester_id),
        render,
        path=f"/portal/approvals/{asset_request.pk}",
    )


def approval_declined(asset_request: AssetRequest) -> None:
    approver = asset_request.approver
    assert approver is not None  # workflow.decline records who declined first

    def render(user: object) -> tuple[str, str]:
        subject = _("Your request %(number)s was declined") % {"number": asset_request.number}
        body = _("%(name)s did not approve your request “%(title)s”.") % {
            "name": approver.display_name,
            "title": asset_request.title,
        }
        if asset_request.approval_comment:
            body += "\n\n" + _("Comment: %(comment)s") % {"comment": asset_request.approval_comment}
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify("request_rejected", [asset_request.requester], render, path=f"/portal/requests/{asset_request.pk}")


def request_assigned(asset_request: AssetRequest) -> None:
    assignee = asset_request.assignee
    assert assignee is not None  # workflow.assign only notifies when someone became the assignee

    def render(user: object) -> tuple[str, str]:
        subject = _("Assigned to you: request %(number)s") % {"number": asset_request.number}
        body = _("You are now responsible for “%(title)s” from %(name)s.") % {
            "title": asset_request.title,
            "name": asset_request.requester.display_name,
        }
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify("assigned_to_me", [assignee], render, path=f"/requests/{asset_request.pk}")


def request_decided(asset_request: AssetRequest) -> None:
    confirmed = asset_request.status == AssetRequestStatus.CONFIRMED

    def render(user: object) -> tuple[str, str]:
        if confirmed:
            subject = _("Your request %(number)s was confirmed") % {"number": asset_request.number}
            body = _("IT confirmed your request “%(title)s” and is preparing it.") % {
                "title": asset_request.title
            }
        else:
            subject = _("Your request %(number)s was declined") % {"number": asset_request.number}
            body = _("IT declined your request “%(title)s”.") % {"title": asset_request.title}
        if asset_request.it_comment:
            body += "\n\n" + _("Comment from IT: %(comment)s") % {"comment": asset_request.it_comment}
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify(
        "request_confirmed" if confirmed else "request_rejected",
        [asset_request.requester],
        render,
        path=f"/portal/requests/{asset_request.pk}",
    )


def request_ready(asset_request: AssetRequest) -> None:
    def render(user: object) -> tuple[str, str]:
        subject = _("Ready for pickup: %(number)s") % {"number": asset_request.number}
        body = _("Everything for “%(title)s” is ready.") % {"title": asset_request.title}
        pickup = _pickup(asset_request)
        return subject, "\n\n".join(part for part in (body, pickup, _items(asset_request)) if part)

    notify("request_ready", [asset_request.requester], render, path=f"/portal/requests/{asset_request.pk}")


def return_reminder(asset_request: AssetRequest) -> None:
    def render(user: object) -> tuple[str, str]:
        subject = _("Return due on %(date)s: %(number)s") % {
            "date": _date(asset_request.end_date),
            "number": asset_request.number,
        }
        body = _("Please return the devices for “%(title)s” by %(date)s.") % {
            "title": asset_request.title,
            "date": _date(asset_request.end_date),
        }
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify(
        "return_reminder",
        [asset_request.requester],
        render,
        key=f"{asset_request.pk}:{asset_request.end_date}",
        path=f"/portal/requests/{asset_request.pk}",
    )


def return_overdue(asset_request: AssetRequest) -> None:
    def render(user: object) -> tuple[str, str]:
        subject = _("Return overdue: %(number)s") % {"number": asset_request.number}
        body = _("The devices for “%(title)s” were due back on %(date)s. Please return them to IT.") % {
            "title": asset_request.title,
            "date": _date(asset_request.end_date),
        }
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify(
        "return_overdue",
        [asset_request.requester],
        render,
        key=f"{asset_request.pk}:{asset_request.end_date}",
        path=f"/portal/requests/{asset_request.pk}",
    )


def return_requested(asset_request: AssetRequest, sender: User) -> None:
    """A reminder IT sends on purpose, e.g. for an overdue return."""

    def render(user: object) -> tuple[str, str]:
        overdue = asset_request.is_overdue
        subject = (_("Return overdue: %(number)s") if overdue else _("Reminder: return of %(number)s")) % {
            "number": asset_request.number
        }
        if overdue:
            body = _("The devices for “%(title)s” were due back on %(date)s. Please return them to IT.")
        else:
            body = _("Please return the devices for “%(title)s” by %(date)s.")
        body %= {"title": asset_request.title, "date": _date(asset_request.end_date)}
        signature = _("Sent by %(name)s, IT") % {"name": sender.display_name}
        return subject, f"{body}\n\n{_items(asset_request)}\n\n{signature}"

    notify(
        "return_requested",
        [asset_request.requester],
        render,
        path=f"/portal/requests/{asset_request.pk}",
        direct=True,
    )


def _devices(labels: list[str]) -> str:
    return "\n".join(f"- {label}" for label in labels)


def request_rescheduled(asset_request: AssetRequest) -> None:
    """IT changed how, when or where the devices reach the employee after the ready message."""

    def render(user: object) -> tuple[str, str]:
        subject = _("Handover changed: %(number)s") % {"number": asset_request.number}
        body = _("IT changed the handover for “%(title)s”.") % {"title": asset_request.title}
        how = asset_request.get_handover_mode_display()
        return subject, "\n\n".join(part for part in (body, how, _pickup(asset_request)) if part)

    notify(
        "request_rescheduled", [asset_request.requester], render, path=f"/portal/requests/{asset_request.pk}"
    )


def request_extended(asset_request: AssetRequest, previous: date | None) -> None:
    def render(user: object) -> tuple[str, str]:
        subject = _("Loan extended: %(number)s") % {"number": asset_request.number}
        body = _("You may keep the devices for “%(title)s” until %(date)s (before: %(previous)s).") % {
            "title": asset_request.title,
            "date": _date(asset_request.end_date),
            "previous": _date(previous),
        }
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify("request_extended", [asset_request.requester], render, path=f"/portal/requests/{asset_request.pk}")


def request_cancelled(asset_request: AssetRequest, by: User | None) -> None:
    """IT withdrew a request; the employee cancelling their own needs no mail."""
    if by is not None and by.pk == asset_request.requester_id:
        return

    def render(user: object) -> tuple[str, str]:
        subject = _("Your request %(number)s was cancelled") % {"number": asset_request.number}
        body = _("IT cancelled your request “%(title)s”.") % {"title": asset_request.title}
        return subject, f"{body}\n\n{_items(asset_request)}"

    notify(
        "request_cancelled", [asset_request.requester], render, path=f"/portal/requests/{asset_request.pk}"
    )


def request_handed_out(asset_request: AssetRequest, devices: list[str], received_by: str) -> None:
    """A record of what the employee received, e.g. to keep for their own files."""

    def render(user: object) -> tuple[str, str]:
        subject = _("Handed out: %(number)s") % {"number": asset_request.number}
        when = formats.date_format(timezone.localtime(asset_request.handed_out_at), "SHORT_DATETIME_FORMAT")
        body = _("These devices for “%(title)s” were handed out on %(when)s:") % {
            "title": asset_request.title,
            "when": when,
        }
        parts = [body, _devices(devices), _("Received by: %(name)s") % {"name": received_by}]
        if asset_request.duration == AssetRequest.Duration.TEMPORARY and asset_request.end_date:
            parts.append(_("Please return them by %(date)s.") % {"date": _date(asset_request.end_date)})
        return subject, "\n\n".join(parts)

    notify(
        "request_handed_out", [asset_request.requester], render, path=f"/portal/requests/{asset_request.pk}"
    )


def request_returned(
    asset_request: AssetRequest, devices: list[str], damaged: list[str], open_: list[str]
) -> None:
    """A record of what IT took back, and what is still out."""

    def render(user: object) -> tuple[str, str]:
        subject = _("Taken back: %(number)s") % {"number": asset_request.number}
        body = _("IT took back these devices for “%(title)s” on %(date)s:") % {
            "title": asset_request.title,
            "date": _date(timezone.localdate()),
        }
        parts = [body, _devices(devices)]
        if damaged:
            parts.append(_("Noted as damaged: %(devices)s") % {"devices": ", ".join(damaged)})
        if open_:
            parts.append(_("Still to return:") + "\n" + _devices(open_))
        return subject, "\n\n".join(parts)

    notify("request_returned", [asset_request.requester], render, path=f"/portal/requests/{asset_request.pk}")

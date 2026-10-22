"""Email notifications about requests (texts rendered in the recipient's language)."""

from django.utils import formats, timezone
from django.utils.translation import gettext as _

from apps.accounts.services.assignment import responsible_staff
from apps.core.notifications import notify
from apps.reservations.models import Reservation


def _items(reservation: Reservation) -> str:
    return "\n".join(f"- {item.quantity_target} × {item.label}" for item in reservation.items.all())


def _date(value) -> str:
    return formats.date_format(value, "SHORT_DATE_FORMAT") if value else "—"


def _pickup(reservation: Reservation) -> str:
    if not reservation.pickup_at:
        return ""
    when = formats.date_format(timezone.localtime(reservation.pickup_at), "SHORT_DATETIME_FORMAT")
    place = f", {reservation.pickup_location.full_name}" if reservation.pickup_location_id else ""
    return _("Pickup: %(when)s%(place)s") % {"when": when, "place": place}


def request_submitted(reservation: Reservation) -> None:
    def render(user):
        subject = _("New request %(number)s from %(name)s") % {
            "number": reservation.number,
            "name": reservation.requester.display_name,
        }
        body = _("%(name)s requests for “%(title)s”:") % {
            "name": reservation.requester.display_name,
            "title": reservation.title,
        }
        return subject, f"{body}\n\n{_items(reservation)}"

    notify(
        "request_submitted",
        responsible_staff(reservation).exclude(pk=reservation.requester_id),
        render,
        path=f"/reservations/{reservation.pk}",
    )


def approval_requested(reservation: Reservation) -> None:
    def render(user):
        subject = _("Approval needed: request %(number)s from %(name)s") % {
            "number": reservation.number,
            "name": reservation.requester.display_name,
        }
        body = _("%(name)s requests for “%(title)s” and needs your approval:") % {
            "name": reservation.requester.display_name,
            "title": reservation.title,
        }
        return subject, f"{body}\n\n{_items(reservation)}"

    notify(
        "approval_requested",
        reservation.approvers().exclude(pk=reservation.requester_id),
        render,
        path=f"/portal/approvals/{reservation.pk}",
    )


def approval_declined(reservation: Reservation) -> None:
    def render(user):
        subject = _("Your request %(number)s was declined") % {"number": reservation.number}
        body = _("%(name)s did not approve your request “%(title)s”.") % {
            "name": reservation.approver.display_name,
            "title": reservation.title,
        }
        if reservation.approval_comment:
            body += "\n\n" + _("Comment: %(comment)s") % {"comment": reservation.approval_comment}
        return subject, f"{body}\n\n{_items(reservation)}"

    notify("request_rejected", [reservation.requester], render, path=f"/portal/requests/{reservation.pk}")


def request_assigned(reservation: Reservation) -> None:
    def render(user):
        subject = _("Assigned to you: request %(number)s") % {"number": reservation.number}
        body = _("You are now responsible for “%(title)s” from %(name)s.") % {
            "title": reservation.title,
            "name": reservation.requester.display_name,
        }
        return subject, f"{body}\n\n{_items(reservation)}"

    notify("assigned_to_me", [reservation.assignee], render, path=f"/reservations/{reservation.pk}")


def request_decided(reservation: Reservation) -> None:
    confirmed = reservation.status == Reservation.Status.CONFIRMED

    def render(user):
        if confirmed:
            subject = _("Your request %(number)s was confirmed") % {"number": reservation.number}
            body = _("IT confirmed your request “%(title)s” and is preparing it.") % {
                "title": reservation.title
            }
        else:
            subject = _("Your request %(number)s was declined") % {"number": reservation.number}
            body = _("IT declined your request “%(title)s”.") % {"title": reservation.title}
        if reservation.it_comment:
            body += "\n\n" + _("Comment from IT: %(comment)s") % {"comment": reservation.it_comment}
        return subject, f"{body}\n\n{_items(reservation)}"

    notify(
        "request_confirmed" if confirmed else "request_rejected",
        [reservation.requester],
        render,
        path=f"/portal/requests/{reservation.pk}",
    )


def request_ready(reservation: Reservation) -> None:
    def render(user):
        subject = _("Ready for pickup: %(number)s") % {"number": reservation.number}
        body = _("Everything for “%(title)s” is ready.") % {"title": reservation.title}
        pickup = _pickup(reservation)
        return subject, "\n\n".join(part for part in (body, pickup, _items(reservation)) if part)

    notify("request_ready", [reservation.requester], render, path=f"/portal/requests/{reservation.pk}")


def return_reminder(reservation: Reservation) -> None:
    def render(user):
        subject = _("Return due on %(date)s: %(number)s") % {
            "date": _date(reservation.end_date),
            "number": reservation.number,
        }
        body = _("Please return the devices for “%(title)s” by %(date)s.") % {
            "title": reservation.title,
            "date": _date(reservation.end_date),
        }
        return subject, f"{body}\n\n{_items(reservation)}"

    notify(
        "return_reminder",
        [reservation.requester],
        render,
        key=f"{reservation.pk}:{reservation.end_date}",
        path=f"/portal/requests/{reservation.pk}",
    )


def return_overdue(reservation: Reservation) -> None:
    def render(user):
        subject = _("Return overdue: %(number)s") % {"number": reservation.number}
        body = _("The devices for “%(title)s” were due back on %(date)s. Please return them to IT.") % {
            "title": reservation.title,
            "date": _date(reservation.end_date),
        }
        return subject, f"{body}\n\n{_items(reservation)}"

    notify(
        "return_overdue",
        [reservation.requester],
        render,
        key=f"{reservation.pk}:{reservation.end_date}",
        path=f"/portal/requests/{reservation.pk}",
    )


def return_requested(reservation: Reservation, sender) -> None:
    """A reminder IT sends on purpose, e.g. for an overdue return."""

    def render(user):
        overdue = reservation.is_overdue
        subject = (_("Return overdue: %(number)s") if overdue else _("Reminder: return of %(number)s")) % {
            "number": reservation.number
        }
        if overdue:
            body = _("The devices for “%(title)s” were due back on %(date)s. Please return them to IT.")
        else:
            body = _("Please return the devices for “%(title)s” by %(date)s.")
        body %= {"title": reservation.title, "date": _date(reservation.end_date)}
        signature = _("Sent by %(name)s, IT") % {"name": sender.display_name}
        return subject, f"{body}\n\n{_items(reservation)}\n\n{signature}"

    notify(
        "return_requested",
        [reservation.requester],
        render,
        path=f"/portal/requests/{reservation.pk}",
        direct=True,
    )


def _devices(labels: list[str]) -> str:
    return "\n".join(f"- {label}" for label in labels)


def request_rescheduled(reservation: Reservation) -> None:
    """IT changed how, when or where the devices reach the employee after the ready message."""

    def render(user):
        subject = _("Handover changed: %(number)s") % {"number": reservation.number}
        body = _("IT changed the handover for “%(title)s”.") % {"title": reservation.title}
        how = reservation.get_handover_mode_display()
        return subject, "\n\n".join(part for part in (body, how, _pickup(reservation)) if part)

    notify("request_rescheduled", [reservation.requester], render, path=f"/portal/requests/{reservation.pk}")


def request_extended(reservation: Reservation, previous) -> None:
    def render(user):
        subject = _("Loan extended: %(number)s") % {"number": reservation.number}
        body = _("You may keep the devices for “%(title)s” until %(date)s (before: %(previous)s).") % {
            "title": reservation.title,
            "date": _date(reservation.end_date),
            "previous": _date(previous),
        }
        return subject, f"{body}\n\n{_items(reservation)}"

    notify("request_extended", [reservation.requester], render, path=f"/portal/requests/{reservation.pk}")


def request_cancelled(reservation: Reservation, by) -> None:
    """IT withdrew a request; the employee cancelling their own needs no mail."""
    if by is not None and by.pk == reservation.requester_id:
        return

    def render(user):
        subject = _("Your request %(number)s was cancelled") % {"number": reservation.number}
        body = _("IT cancelled your request “%(title)s”.") % {"title": reservation.title}
        return subject, f"{body}\n\n{_items(reservation)}"

    notify("request_cancelled", [reservation.requester], render, path=f"/portal/requests/{reservation.pk}")


def request_handed_out(reservation: Reservation, devices: list[str], received_by: str) -> None:
    """A record of what the employee received, e.g. to keep for their own files."""

    def render(user):
        subject = _("Handed out: %(number)s") % {"number": reservation.number}
        when = formats.date_format(timezone.localtime(reservation.handed_out_at), "SHORT_DATETIME_FORMAT")
        body = _("These devices for “%(title)s” were handed out on %(when)s:") % {
            "title": reservation.title,
            "when": when,
        }
        parts = [body, _devices(devices), _("Received by: %(name)s") % {"name": received_by}]
        if reservation.duration == Reservation.Duration.TEMPORARY and reservation.end_date:
            parts.append(_("Please return them by %(date)s.") % {"date": _date(reservation.end_date)})
        return subject, "\n\n".join(parts)

    notify("request_handed_out", [reservation.requester], render, path=f"/portal/requests/{reservation.pk}")


def request_returned(
    reservation: Reservation, devices: list[str], damaged: list[str], open_: list[str]
) -> None:
    """A record of what IT took back, and what is still out."""

    def render(user):
        subject = _("Taken back: %(number)s") % {"number": reservation.number}
        body = _("IT took back these devices for “%(title)s” on %(date)s:") % {
            "title": reservation.title,
            "date": _date(timezone.localdate()),
        }
        parts = [body, _devices(devices)]
        if damaged:
            parts.append(_("Noted as damaged: %(devices)s") % {"devices": ", ".join(damaged)})
        if open_:
            parts.append(_("Still to return:") + "\n" + _devices(open_))
        return subject, "\n\n".join(parts)

    notify("request_returned", [reservation.requester], render, path=f"/portal/requests/{reservation.pk}")

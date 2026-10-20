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
    approved = reservation.status == Reservation.Status.APPROVED

    def render(user):
        if approved:
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
        "request_approved" if approved else "request_rejected",
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

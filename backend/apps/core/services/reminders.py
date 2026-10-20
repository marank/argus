"""Time-based email notifications, queued by the hourly ``send_reminders`` job.

Each reminder goes out once per recipient (see ``NotificationLog``), so running
this more often or catching up after a pause is safe.
"""

from datetime import timedelta

from django.utils import timezone

from apps.core.features import is_enabled
from apps.core.models import SiteSettings
from apps.inventory.models import License
from apps.inventory.services import notifications as inventory_notifications
from apps.reservations.models import Reservation
from apps.reservations.services import notifications as reservation_notifications


def send_due_reminders() -> int:
    """Queue due return reminders, overdue notices and license expiry warnings; returns the number checked."""
    settings = SiteSettings.load()
    today = timezone.localdate()
    checked = 0

    lent = Reservation.objects.filter(
        duration=Reservation.Duration.TEMPORARY, status=Reservation.Status.HANDED_OUT
    ).select_related("requester")
    due_soon = lent.filter(end_date__range=(today, today + timedelta(days=settings.return_reminder_days)))
    for reservation in due_soon:
        reservation_notifications.return_reminder(reservation)
        checked += 1
    for reservation in lent.filter(end_date__lt=today):
        reservation_notifications.return_overdue(reservation)
        checked += 1

    if is_enabled("licenses"):
        ending = License.objects.select_related("model__manufacturer").filter(
            valid_until__range=(today, today + timedelta(days=settings.license_warning_days))
        )
        for license in ending:
            inventory_notifications.license_expiring(license)
            checked += 1

    return checked

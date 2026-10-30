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
from apps.requests.models import AssetRequest, AssetRequestStatus
from apps.requests.services import notifications as asset_request_notifications


def send_due_reminders() -> int:
    """Queue due return reminders, overdue notices and license expiry warnings; returns the number checked."""
    settings = SiteSettings.load()
    today = timezone.localdate()
    checked = 0

    lent = AssetRequest.objects.filter(
        duration=AssetRequest.Duration.TEMPORARY, status=AssetRequestStatus.HANDED_OUT
    ).select_related("requester")
    due_soon = lent.filter(end_date__range=(today, today + timedelta(days=settings.return_reminder_days)))
    for asset_request in due_soon:
        asset_request_notifications.return_reminder(asset_request)
        checked += 1
    for asset_request in lent.filter(end_date__lt=today):
        asset_request_notifications.return_overdue(asset_request)
        checked += 1

    if is_enabled("licenses"):
        ending = License.objects.select_related("model__manufacturer").filter(
            valid_until__range=(today, today + timedelta(days=settings.license_warning_days))
        )
        for license in ending:
            inventory_notifications.license_expiring(license)
            checked += 1

    return checked

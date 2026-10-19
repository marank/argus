from datetime import date

from django.http import HttpRequest
from django.utils.translation import gettext as _
from ninja import Query, Router
from ninja.errors import HttpError

from apps.core.api.security import it_staff_auth
from apps.core.features import current_flags
from apps.dashboard.schemas.calendar import CalendarEntryOut
from apps.dashboard.services.calendar import KINDS, calendar_entries

# Calendar kinds that can be switched off in the site settings.
KIND_FEATURES = {
    "warranty": "calendar_warranty",
    "license": "calendar_license_expiry",
    "delivery": "calendar_deliveries",
}

router = Router(tags=["calendar"], auth=it_staff_auth)

MAX_DAYS = 400


@router.get("", response=list[CalendarEntryOut])
def calendar(request: HttpRequest, start: date, end: date, kinds: Query[list[str]] = None):
    """Lending periods, pickups, due returns, expected deliveries and warranty ends."""
    if end < start or (end - start).days > MAX_DAYS:
        raise HttpError(422, _("Choose a range of at most %(days)s days.") % {"days": MAX_DAYS})
    flags = current_flags()
    available = {k for k in KINDS if flags.get(KIND_FEATURES.get(k, ""), True)}
    selected = {k for k in (kinds or []) if k in available} or available
    return calendar_entries(start, end, selected)

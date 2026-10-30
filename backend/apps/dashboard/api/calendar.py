from datetime import date

from django.utils.translation import gettext as _
from ninja import Query, Router
from ninja.errors import HttpError

from apps.accounts.permissions import ResourceKey
from apps.accounts.services.assignment import Assigned, assigned_q
from apps.core.api.security import AuthedRequest, permission_auth
from apps.core.features import FeatureKey, current_flags
from apps.dashboard.schemas.calendar import CalendarEntryOut
from apps.dashboard.services.calendar import KINDS, Entry, calendar_entries

# Calendar kinds that can be switched off in the site settings.
# Kinds that a feature switches on and off; the others follow the calendar module only.
KIND_FEATURES: dict[str, FeatureKey] = {
    "warranty": FeatureKey.CALENDAR_WARRANTY,
    "license": FeatureKey.CALENDAR_LICENSE_EXPIRY,
    "delivery": FeatureKey.CALENDAR_DELIVERIES,
}

router = Router(tags=["calendar"], auth=permission_auth(ResourceKey.REQUESTS))

MAX_DAYS = 400


@router.get("", response=list[CalendarEntryOut])
def calendar(
    request: AuthedRequest,
    start: date,
    end: date,
    kinds: Query[list[str] | None] = None,
    assigned: Assigned | None = None,
) -> list[Entry]:
    """Lending periods, pickups, due returns, expected deliveries and warranty ends.

    ``assigned`` (``me``, ``my_teams``, ``nobody``) narrows the request entries.
    """
    if end < start or (end - start).days > MAX_DAYS:
        raise HttpError(422, _("Choose a range of at most %(days)s days.") % {"days": MAX_DAYS})
    flags = current_flags()
    available = {k for k in KINDS if k not in KIND_FEATURES or flags[KIND_FEATURES[k]]}
    selected = {k for k in (kinds or []) if k in available} or available
    return calendar_entries(start, end, selected, assigned_q(request.user, assigned))

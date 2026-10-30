"""Modules and features that administrators switch on and off in the site settings.

A *module* is a whole area (pages, API, sidebar entry). A *feature* is a smaller
behaviour inside one or more modules; it only takes effect while all modules it
requires are on. Everything is on by default.
"""

import re
from dataclasses import dataclass
from enum import StrEnum


class ModuleKey(StrEnum):
    CONSUMABLES = "consumables"
    LICENSES = "licenses"
    PROCUREMENT = "procurement"
    CALENDAR = "calendar"
    ISSUES = "issues"
    TERMINAL = "terminal"


class FeatureKey(StrEnum):
    CALENDAR_WARRANTY = "calendar_warranty"
    CALENDAR_LICENSE_EXPIRY = "calendar_license_expiry"
    CALENDAR_DELIVERIES = "calendar_deliveries"
    CONSUMABLE_QUICK_PICK = "consumable_quick_pick"
    SOFTWARE_REQUESTS = "software_requests"
    ATTENTION_MOTION = "attention_motion"


type FlagKey = ModuleKey | FeatureKey


class FlagKind(StrEnum):
    MODULE = "module"
    FEATURE = "feature"


@dataclass(frozen=True)
class Flag:
    key: FlagKey
    # Modules that must be on for a feature to take effect.
    requires: tuple[ModuleKey, ...] = ()

    @property
    def kind(self) -> FlagKind:
        return FlagKind.MODULE if isinstance(self.key, ModuleKey) else FlagKind.FEATURE


FLAGS: tuple[Flag, ...] = (
    *(Flag(module) for module in ModuleKey),
    Flag(FeatureKey.CALENDAR_WARRANTY, (ModuleKey.CALENDAR,)),
    Flag(FeatureKey.CALENDAR_LICENSE_EXPIRY, (ModuleKey.CALENDAR, ModuleKey.LICENSES)),
    Flag(FeatureKey.CALENDAR_DELIVERIES, (ModuleKey.CALENDAR, ModuleKey.PROCUREMENT)),
    Flag(FeatureKey.CONSUMABLE_QUICK_PICK, (ModuleKey.CONSUMABLES,)),
    Flag(FeatureKey.SOFTWARE_REQUESTS, (ModuleKey.LICENSES,)),
    Flag(FeatureKey.ATTENTION_MOTION),
)
FLAG_KEYS: set[FlagKey] = {flag.key for flag in FLAGS}


def effective_flags(stored: dict[str, object]) -> dict[FlagKey, bool]:
    """Stored switches with defaults, features off while a required module is off."""
    values = {flag.key: bool(stored.get(flag.key, True)) for flag in FLAGS}
    for flag in FLAGS:
        if flag.requires and not all(values[module] for module in flag.requires):
            values[flag.key] = False
    return values


def current_flags() -> dict[FlagKey, bool]:
    from apps.core.models import SiteSettings

    return effective_flags(SiteSettings.load().flags)


def is_enabled(key: FlagKey) -> bool:
    return current_flags()[key]


# API paths that belong to a module or feature; disabled ones answer 404.
GUARDED_PATHS: tuple[tuple[re.Pattern[str], FlagKey], ...] = tuple(
    (re.compile(pattern), key)
    for pattern, key in (
        (r"^/api/inventory/consumables", ModuleKey.CONSUMABLES),
        (r"^/api/portal/my-consumables", FeatureKey.CONSUMABLE_QUICK_PICK),
        (r"^/api/inventory/licenses", ModuleKey.LICENSES),
        (r"^/api/portal/my-licenses", ModuleKey.LICENSES),
        (r"^/api/procurement", ModuleKey.PROCUREMENT),
        (r"^/api/calendar", ModuleKey.CALENDAR),
        (r"^/api/inventory/issues", ModuleKey.ISSUES),
        (r"^/api/portal/my-issues", ModuleKey.ISSUES),
        (r"^/api/portal/my-assets/[^/]+/issues", ModuleKey.ISSUES),
        (r"^/api/terminal", ModuleKey.TERMINAL),
    )
)


def guard_for(path: str) -> FlagKey | None:
    return next((key for pattern, key in GUARDED_PATHS if pattern.match(path)), None)

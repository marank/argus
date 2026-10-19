"""Modules and features that administrators switch on and off in the site settings.

A *module* is a whole area (pages, API, sidebar entry). A *feature* is a smaller
behaviour inside one or more modules; it only takes effect while all modules it
requires are on. Everything is on by default.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Flag:
    key: str
    kind: str  # "module" or "feature"
    requires: tuple[str, ...] = ()


FLAGS: tuple[Flag, ...] = (
    Flag("consumables", "module"),
    Flag("licenses", "module"),
    Flag("procurement", "module"),
    Flag("calendar", "module"),
    Flag("issues", "module"),
    Flag("terminal", "module"),
    Flag("calendar_warranty", "feature", ("calendar",)),
    Flag("calendar_license_expiry", "feature", ("calendar", "licenses")),
    Flag("calendar_deliveries", "feature", ("calendar", "procurement")),
    Flag("consumable_quick_pick", "feature", ("consumables",)),
    Flag("software_requests", "feature", ("licenses",)),
    Flag("attention_motion", "feature"),
)
FLAG_KEYS = {flag.key for flag in FLAGS}


def effective_flags(stored: dict) -> dict[str, bool]:
    """Stored switches with defaults, features off while a required module is off."""
    values = {flag.key: bool(stored.get(flag.key, True)) for flag in FLAGS}
    for flag in FLAGS:
        if flag.requires and not all(values[module] for module in flag.requires):
            values[flag.key] = False
    return values


def current_flags() -> dict[str, bool]:
    from apps.core.models import SiteSettings

    return effective_flags(SiteSettings.load().flags)


def is_enabled(key: str) -> bool:
    return current_flags()[key]


# API paths that belong to a module or feature; disabled ones answer 404.
GUARDED_PATHS: tuple[tuple[re.Pattern, str], ...] = tuple(
    (re.compile(pattern), key)
    for pattern, key in (
        (r"^/api/inventory/consumables", "consumables"),
        (r"^/api/portal/my-consumables", "consumable_quick_pick"),
        (r"^/api/inventory/licenses", "licenses"),
        (r"^/api/portal/my-licenses", "licenses"),
        (r"^/api/procurement", "procurement"),
        (r"^/api/calendar", "calendar"),
        (r"^/api/inventory/issues", "issues"),
        (r"^/api/portal/my-issues", "issues"),
        (r"^/api/portal/my-assets/[^/]+/issues", "issues"),
        (r"^/api/terminal", "terminal"),
    )
)


def guard_for(path: str) -> str | None:
    return next((key for pattern, key in GUARDED_PATHS if pattern.match(path)), None)

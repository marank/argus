"""What IT staff may do, per area of the app, granted through roles.

The areas are fixed here because only what the API checks can be granted;
administrators combine them into roles (``Role.permissions``). A user's rights
are the highest level any of their roles gives per area. Administrators may do
everything, and only IT staff can hold rights at all.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from apps.accounts.models import User

READ = "read"
WRITE = "write"
LEVELS = (READ, WRITE)
_RANK: dict[str | None, int] = {None: 0, READ: 1, WRITE: 2}


@dataclass(frozen=True)
class Resource:
    key: str
    group: str  # "masterdata" or "operations", for grouping in the role editor


RESOURCES: tuple[Resource, ...] = (
    Resource("models", "masterdata"),
    Resource("categories", "masterdata"),
    Resource("manufacturers", "masterdata"),
    Resource("suppliers", "masterdata"),
    Resource("locations", "masterdata"),
    Resource("departments", "masterdata"),
    Resource("teams", "masterdata"),
    Resource("users", "masterdata"),
    Resource("number_sequences", "masterdata"),
    Resource("requests", "operations"),
    Resource("assets", "operations"),
    Resource("consumables", "operations"),
    Resource("licenses", "operations"),
    Resource("issues", "operations"),
    Resource("procurement", "operations"),
)
RESOURCE_KEYS = {resource.key for resource in RESOURCES}


def clean_permissions(value: object) -> dict[str, str]:
    """Only known areas with a valid level; anything else is dropped."""
    if not isinstance(value, dict):
        return {}
    return {key: level for key, level in value.items() if key in RESOURCE_KEYS and level in LEVELS}


def effective_permissions(user: User | AnonymousUser | None) -> dict[str, str]:
    """The user's level per area (areas without any right are left out).

    Cached on the user object, so one request asks the database once.
    """
    if not (user and user.is_authenticated):
        return {}
    if user._argus_permissions is not None:
        return user._argus_permissions
    if user.is_superuser:
        result: dict[str, str] = {key: WRITE for key in RESOURCE_KEYS}
    elif not user.is_staff:
        result = {}
    else:
        result = {}
        for permissions in user.roles.values_list("permissions", flat=True):
            for key, level in clean_permissions(permissions).items():
                if _RANK[level] > _RANK[result.get(key)]:
                    result[key] = level
    user._argus_permissions = result
    return result


def can(user: User | AnonymousUser | None, resource: str, level: str = READ) -> bool:
    return _RANK[effective_permissions(user).get(resource)] >= _RANK[level]

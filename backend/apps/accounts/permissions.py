"""What IT staff may do, per area of the app, granted through roles.

The areas are fixed here because only what the API checks can be granted;
administrators combine them into roles (``Role.permissions``). A user's rights
are the highest level any of their roles gives per area. Administrators may do
everything, and only IT staff can hold rights at all.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from apps.accounts.models import User


class ResourceKey(StrEnum):
    """Areas of the app that roles grant rights on."""

    MODELS = "models"
    CATEGORIES = "categories"
    MANUFACTURERS = "manufacturers"
    SUPPLIERS = "suppliers"
    LOCATIONS = "locations"
    DEPARTMENTS = "departments"
    TEAMS = "teams"
    USERS = "users"
    NUMBER_SEQUENCES = "number_sequences"
    REQUESTS = "requests"
    ASSETS = "assets"
    CONSUMABLES = "consumables"
    LICENSES = "licenses"
    ISSUES = "issues"
    PROCUREMENT = "procurement"


class PermissionLevel(StrEnum):
    READ = "read"
    WRITE = "write"


class ResourceGroup(StrEnum):
    """Grouping in the role editor."""

    MASTERDATA = "masterdata"
    OPERATIONS = "operations"


_RANK: dict[PermissionLevel | None, int] = {None: 0, PermissionLevel.READ: 1, PermissionLevel.WRITE: 2}


@dataclass(frozen=True)
class Resource:
    key: ResourceKey
    group: ResourceGroup


_MASTERDATA = {
    ResourceKey.MODELS,
    ResourceKey.CATEGORIES,
    ResourceKey.MANUFACTURERS,
    ResourceKey.SUPPLIERS,
    ResourceKey.LOCATIONS,
    ResourceKey.DEPARTMENTS,
    ResourceKey.TEAMS,
    ResourceKey.USERS,
    ResourceKey.NUMBER_SEQUENCES,
}
RESOURCES: tuple[Resource, ...] = tuple(
    Resource(key, ResourceGroup.MASTERDATA if key in _MASTERDATA else ResourceGroup.OPERATIONS)
    for key in ResourceKey
)


def clean_permissions(value: object) -> dict[ResourceKey, PermissionLevel]:
    """Only known areas with a valid level; anything else is dropped."""
    if not isinstance(value, dict):
        return {}
    return {
        ResourceKey(key): PermissionLevel(level)
        for key, level in value.items()
        if key in ResourceKey and level in PermissionLevel
    }


def effective_permissions(user: User | AnonymousUser | None) -> dict[ResourceKey, PermissionLevel]:
    """The user's level per area (areas without any right are left out).

    Cached on the user object, so one request asks the database once.
    """
    if not (user and user.is_authenticated):
        return {}
    if user._argus_permissions is not None:
        return user._argus_permissions
    if user.is_superuser:
        result: dict[ResourceKey, PermissionLevel] = dict.fromkeys(ResourceKey, PermissionLevel.WRITE)
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


def can(
    user: User | AnonymousUser | None, resource: ResourceKey, level: PermissionLevel = PermissionLevel.READ
) -> bool:
    return _RANK[effective_permissions(user).get(resource)] >= _RANK[level]

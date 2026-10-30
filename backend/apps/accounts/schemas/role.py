from uuid import UUID

from apps.accounts.models import Role, User
from apps.accounts.permissions import PermissionLevel, ResourceGroup, ResourceKey, clean_permissions
from apps.core.schemas.base import Schema

from .user import UserRefOut


class RoleOut(Schema):
    id: UUID
    name: str
    description: str
    # Area → "read" or "write"; areas left out are not accessible.
    permissions: dict[ResourceKey, PermissionLevel]
    members: list[UserRefOut]

    @staticmethod
    def resolve_permissions(obj: Role) -> dict[ResourceKey, PermissionLevel]:
        # Stored rights of areas that no longer exist are not sent.
        return clean_permissions(obj.permissions)

    @staticmethod
    def resolve_members(obj: Role) -> list[User]:
        return list(obj.members.all())


class RoleIn(Schema):
    name: str
    description: str = ""
    permissions: dict[str, str] = {}
    members: list[UUID] = []


class ResourceOut(Schema):
    key: ResourceKey
    group: ResourceGroup

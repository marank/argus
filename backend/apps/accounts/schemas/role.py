from uuid import UUID

from ninja import Schema

from .user import UserRefOut


class RoleOut(Schema):
    id: UUID
    name: str
    description: str
    # Area → "read" or "write"; areas left out are not accessible.
    permissions: dict[str, str]
    members: list[UserRefOut]

    @staticmethod
    def resolve_members(obj) -> list:
        return list(obj.members.all())


class RoleIn(Schema):
    name: str
    description: str = ""
    permissions: dict[str, str] = {}
    members: list[UUID] = []


class ResourceOut(Schema):
    key: str
    group: str

from uuid import UUID

from ninja import Schema

from .user import UserRefOut


class TeamRefOut(Schema):
    id: UUID
    name: str
    code: str


class TeamOut(TeamRefOut):
    sort_order: int
    ldap_group_dn: str
    is_default: bool
    members: list[UserRefOut]

    @staticmethod
    def resolve_members(obj) -> list:
        return list(obj.members.all())


class TeamIn(Schema):
    name: str
    code: str = ""
    sort_order: int = 0
    ldap_group_dn: str = ""
    is_default: bool = False
    members: list[UUID] = []

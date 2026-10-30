from typing import Any
from uuid import UUID

from ninja import Schema

from apps.accounts.models import Team, User
from apps.core.schemas import per_response

from .user import UserRefOut


def default_team(context: dict[str, Any] | None) -> Team | None:
    """For schema resolvers: the team that gets what no model or category assigns."""
    return per_response(context, "default_team", lambda: Team.objects.filter(is_default=True).first())


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
    def resolve_members(obj: Team) -> list[User]:
        return list(obj.members.all())


class TeamIn(Schema):
    name: str
    code: str = ""
    sort_order: int = 0
    ldap_group_dn: str = ""
    is_default: bool = False
    members: list[UUID] = []

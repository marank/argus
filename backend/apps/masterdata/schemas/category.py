from typing import Any
from uuid import UUID

from ninja import Schema

from apps.accounts.models import Team
from apps.accounts.schemas import TeamRefOut, default_team
from apps.core.api.security import context_is_it_staff
from apps.core.schemas import RefOut
from apps.masterdata.models import Category


class CategoryOut(Schema):
    id: UUID
    name: str
    kind: str
    item_name: str
    code: str
    parent: RefOut | None
    description: str
    icon: str
    number_sequence: RefOut | None
    is_requestable: bool
    allow_any_model: bool
    requires_approval: bool
    # Whether requests need approval, here or because of a category above.
    needs_approval: bool
    sort_order: int
    path: list[str]
    # IT-internal: empty for employees.
    team: TeamRefOut | None = None
    # The team that applies: the own, the nearest parent's or the default team; IT-internal as well.
    effective_team: TeamRefOut | None = None

    @staticmethod
    def resolve_team(obj: Category, context: dict[str, Any] | None) -> Team | None:
        return obj.team if context_is_it_staff(context) else None

    @staticmethod
    def resolve_needs_approval(obj: Category) -> bool:
        return obj.needs_approval()

    @staticmethod
    def resolve_effective_team(obj: Category, context: dict[str, Any] | None) -> Team | None:
        if not context_is_it_staff(context):
            return None
        return obj.effective_team() or default_team(context)

    @staticmethod
    def resolve_path(obj: Category) -> list[str]:
        return [c.name for c in reversed(obj.ancestors())] + [obj.name]


class CategoryIn(Schema):
    name: str
    kind: Category.Kind = Category.Kind.HARDWARE
    item_name: str = ""
    code: str = ""
    parent: UUID | None = None
    description: str = ""
    icon: str = ""
    number_sequence: UUID | None = None
    is_requestable: bool = True
    allow_any_model: bool = True
    requires_approval: bool = False
    team: UUID | None = None
    sort_order: int = 0

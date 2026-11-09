from typing import Any
from uuid import UUID

from apps.accounts.models import Team
from apps.accounts.schemas import TeamRefOut, default_team
from apps.core.api.security import context_is_it_staff
from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.masterdata.models import Category, CategoryKind, DeviceNaming, ModelChoice


class CategoryOut(Schema):
    id: UUID
    name: str
    kind: CategoryKind
    item_name: str
    code: str
    identifier_label: str
    parent: RefOut | None
    description: str
    icon: str
    number_sequence: RefOut | None
    device_naming: DeviceNaming
    name_sequence: RefOut | None
    is_requestable: bool
    model_choice: ModelChoice
    requires_approval: bool
    is_accessory: bool
    # Whether requests need approval, here or because of a category above.
    needs_approval: bool
    # Whether it holds accessories, here or because of a category above.
    holds_accessories: bool
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
    def resolve_holds_accessories(obj: Category) -> bool:
        return obj.holds_accessories()

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
    kind: CategoryKind = CategoryKind.HARDWARE
    item_name: str = ""
    code: str = ""
    identifier_label: str = ""
    parent: UUID | None = None
    description: str = ""
    icon: str = ""
    number_sequence: UUID | None = None
    device_naming: DeviceNaming = DeviceNaming.NONE
    name_sequence: UUID | None = None
    is_requestable: bool = True
    model_choice: ModelChoice = ModelChoice.ANY_OR_SPECIFIC
    requires_approval: bool = False
    is_accessory: bool = False
    team: UUID | None = None
    sort_order: int = 0

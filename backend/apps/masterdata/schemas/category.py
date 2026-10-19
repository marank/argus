from uuid import UUID

from ninja import Schema

from apps.core.schemas import RefOut


class CategoryOut(Schema):
    id: UUID
    name: str
    code: str
    parent: RefOut | None
    description: str
    icon: str
    number_sequence: RefOut | None
    is_requestable: bool
    allow_any_model: bool
    sort_order: int
    path: list[str]

    @staticmethod
    def resolve_path(obj) -> list[str]:
        return [c.name for c in reversed(obj.ancestors())] + [obj.name]


class CategoryIn(Schema):
    name: str
    code: str
    parent: UUID | None = None
    description: str = ""
    icon: str = ""
    number_sequence: UUID | None = None
    is_requestable: bool = True
    allow_any_model: bool = True
    sort_order: int = 0

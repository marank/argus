from uuid import UUID

from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema
from apps.masterdata.models import Category, ComponentType


class ComponentTypeOut(Schema):
    id: UUID
    name: str
    categories: list[RefOut]
    sort_order: int

    @staticmethod
    def resolve_categories(obj: ComponentType) -> list[Category]:
        return list(obj.categories.all())


class ComponentTypeIn(Schema):
    name: str
    categories: list[UUID] = []
    sort_order: int = 0

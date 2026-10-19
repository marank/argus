from typing import Annotated
from uuid import UUID

from ninja import FilterLookup, FilterSchema

from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import Category
from apps.masterdata.schemas.category import CategoryIn, CategoryOut


class CategoryFilter(FilterSchema):
    parent: Annotated[UUID | None, FilterLookup("parent_id")] = None
    is_requestable: bool | None = None
    kind: str | None = None


router = build_crud_router(
    CrudConfig(
        model=Category,
        out_schema=CategoryOut,
        in_schema=CategoryIn,
        filter_schema=CategoryFilter,
        search_fields=("name", "code", "description"),
        ordering_fields=("name", "code", "sort_order", "kind"),
        queryset=lambda: Category.objects.select_related("parent__parent", "number_sequence"),
    ),
    tags=["categories"],
)

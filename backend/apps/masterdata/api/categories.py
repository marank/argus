from typing import Annotated
from uuid import UUID

from django.db.models import Case, IntegerField, Value, When
from ninja import FilterLookup, FilterSchema

from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import Category
from apps.masterdata.schemas.category import CategoryIn, CategoryOut


class CategoryFilter(FilterSchema):
    parent: Annotated[UUID | None, FilterLookup("parent_id")] = None
    is_requestable: bool | None = None
    kind: str | None = None


def category_queryset():
    # `tree_position`: parents before their subcategories; the default order of every list.
    positions = Category.tree_positions()
    return (
        Category.objects.select_related("parent__parent", "number_sequence", "team")
        .annotate(
            tree_position=Case(
                *[When(pk=pk, then=Value(position)) for pk, position in positions.items()],
                default=Value(len(positions)),
                output_field=IntegerField(),
            )
        )
        .order_by("tree_position")
    )


router = build_crud_router(
    CrudConfig(
        model=Category,
        out_schema=CategoryOut,
        in_schema=CategoryIn,
        filter_schema=CategoryFilter,
        permission="categories",
        search_fields=("name", "code", "description"),
        ordering_fields=("name", "code", "sort_order", "kind", "tree_position"),
        queryset=category_queryset,
    ),
    tags=["categories"],
)

from uuid import UUID

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from ninja import FilterSchema

from apps.accounts.permissions import ResourceKey
from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import Category, ComponentType
from apps.masterdata.schemas.component_type import ComponentTypeIn, ComponentTypeOut


class ComponentTypeFilter(FilterSchema):
    # The parts devices of this category have, including those assigned to a category above it.
    category: UUID | None = None

    def filter_category(self, value: UUID | None) -> Q:
        if not value:
            return Q()
        category = get_object_or_404(Category, pk=value)
        return Q(pk__in=ComponentType.for_category(category).values("pk"))


def component_type_queryset() -> QuerySet[ComponentType]:
    return ComponentType.objects.prefetch_related("categories")


router = build_crud_router(
    CrudConfig(
        model=ComponentType,
        out_schema=ComponentTypeOut,
        in_schema=ComponentTypeIn,
        filter_schema=ComponentTypeFilter,
        # Part of setting up the categories.
        permission=ResourceKey.CATEGORIES,
        search_fields=("name",),
        ordering_fields=("name", "sort_order"),
        queryset=component_type_queryset,
    ),
    tags=["component types"],
)

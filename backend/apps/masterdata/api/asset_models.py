from typing import Annotated
from uuid import UUID

from django.db.models import Q
from ninja import FilterLookup, FilterSchema

from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import AssetModel
from apps.masterdata.schemas.asset_model import AssetModelIn, AssetModelOut


class AssetModelFilter(FilterSchema):
    manufacturer: Annotated[UUID | None, FilterLookup("manufacturer_id")] = None
    category: Annotated[UUID | None, FilterLookup("category_id")] = None
    tracking: str | None = None
    ean: str | None = None
    is_active: bool | None = None
    is_requestable: bool | None = None
    # Only models that draw inventory numbers from a sequence of their own or of their category.
    numbered: bool | None = None

    def filter_numbered(self, value: bool | None) -> Q:
        if value is None:
            return Q()
        q = Q(number_sequence__isnull=False) | Q(category__number_sequence__isnull=False)
        return q if value else ~q


router = build_crud_router(
    CrudConfig(
        model=AssetModel,
        out_schema=AssetModelOut,
        in_schema=AssetModelIn,
        filter_schema=AssetModelFilter,
        permission="models",
        search_fields=("name", "designation", "manufacturer__name", "part_number", "ean", "category__name"),
        ordering_fields=(
            "name",
            "designation",
            "manufacturer__name",
            "category__name",
            "category__kind",
            "category__sort_order",
            "part_number",
        ),
        queryset=lambda: AssetModel.objects.select_related(
            "manufacturer", "category__number_sequence", "default_supplier", "team", "number_sequence"
        ).prefetch_related("compatible_with__manufacturer"),
    ),
    tags=["asset models"],
)

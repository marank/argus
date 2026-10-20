from typing import Annotated
from uuid import UUID

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


router = build_crud_router(
    CrudConfig(
        model=AssetModel,
        out_schema=AssetModelOut,
        in_schema=AssetModelIn,
        filter_schema=AssetModelFilter,
        permission="models",
        search_fields=("name", "manufacturer__name", "part_number", "ean", "category__name"),
        ordering_fields=(
            "name",
            "manufacturer__name",
            "category__name",
            "category__kind",
            "category__sort_order",
            "part_number",
        ),
        queryset=lambda: AssetModel.objects.select_related(
            "manufacturer", "category", "default_supplier", "team"
        ).prefetch_related("compatible_with__manufacturer"),
    ),
    tags=["asset models"],
)

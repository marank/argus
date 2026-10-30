from ninja import FilterSchema

from apps.accounts.permissions import ResourceKey
from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import Manufacturer
from apps.masterdata.schemas.manufacturer import ManufacturerIn, ManufacturerOut


class ManufacturerFilter(FilterSchema):
    is_active: bool | None = None


router = build_crud_router(
    CrudConfig(
        model=Manufacturer,
        out_schema=ManufacturerOut,
        in_schema=ManufacturerIn,
        filter_schema=ManufacturerFilter,
        permission=ResourceKey.MANUFACTURERS,
        search_fields=("name", "website"),
    ),
    tags=["manufacturers"],
)

from ninja import FilterSchema

from apps.core.api.crud import CrudConfig, build_crud_router
from apps.masterdata.models import Supplier
from apps.masterdata.schemas.supplier import SupplierIn, SupplierOut


class SupplierFilter(FilterSchema):
    is_active: bool | None = None


router = build_crud_router(
    CrudConfig(
        model=Supplier,
        out_schema=SupplierOut,
        in_schema=SupplierIn,
        filter_schema=SupplierFilter,
        search_fields=("name", "customer_number", "contact_person", "email"),
        ordering_fields=("name", "customer_number", "contact_person"),
    ),
    tags=["suppliers"],
)

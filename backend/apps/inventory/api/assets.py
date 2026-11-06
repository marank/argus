from datetime import date
from typing import Annotated
from uuid import UUID

from django.db.models import Prefetch, ProtectedError, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.accounts.permissions import ResourceKey
from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import AuthedRequest, permission_auth
from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset
from apps.inventory.schemas.asset import (
    AssetAssignIn,
    AssetBulkIn,
    AssetDetailOut,
    AssetIn,
    AssetOut,
    AssetSeriesIn,
    AssetSeriesPreviewOut,
)
from apps.inventory.services import assets as asset_service
from apps.masterdata.models import AssetModel, Category
from apps.requests.models import AssetRequestAllocation

router = Router(tags=["assets"], auth=permission_auth(ResourceKey.ASSETS))

SEARCH_FIELDS = (
    "inventory_number",
    "serial_number",
    "identifier",
    "installed_components__serial_number",
    "imei",
    "mac_address",
    "hostname",
    "model__name",
    "model__manufacturer__name",
    "assigned_to__first_name",
    "assigned_to__last_name",
    "assigned_to__username",
)
ORDERING_FIELDS = (
    "inventory_number",
    "model__category__sort_order",
    "model__category__name",
    "serial_number",
    "identifier",
    "status",
    "model__name",
    "location__name",
    "assigned_to__last_name",
    # Ties broken by the record, so the rows of a grouping stay together.
    "model__manufacturer__name",
    "model_id",
    "location_id",
    "assigned_to__first_name",
    "assigned_to_id",
    "warranty_until",
    "purchase_date",
    "created_at",
)


class AssetFilter(FilterSchema):
    status: Annotated[list[str] | None, FilterLookup("status__in")] = None
    model: Annotated[list[UUID] | None, FilterLookup("model_id__in")] = None
    manufacturer: Annotated[list[UUID] | None, FilterLookup("model__manufacturer_id__in")] = None
    location: Annotated[list[UUID] | None, FilterLookup("location_id__in")] = None
    assigned_to: Annotated[list[UUID] | None, FilterLookup("assigned_to_id__in")] = None
    is_loanable: bool | None = None
    tracking: Annotated[str | None, FilterLookup("model__tracking")] = None
    warranty_from: Annotated[date | None, FilterLookup("warranty_until__gte")] = None
    warranty_until: Annotated[date | None, FilterLookup("warranty_until__lte")] = None
    supplier: Annotated[list[UUID] | None, FilterLookup("supplier_id__in")] = None
    purchase_from: Annotated[date | None, FilterLookup("purchase_date__gte")] = None
    purchase_until: Annotated[date | None, FilterLookup("purchase_date__lte")] = None
    category: list[UUID] | None = None

    def filter_category(self, value: list[UUID] | None) -> Q:
        if not value:
            return Q()
        return Q(model__category_id__in=Category.descendant_ids_of(value))


def asset_queryset() -> QuerySet[Asset]:
    return Asset.objects.select_related(
        "model__manufacturer",
        "model__category",
        "location__parent",
        "assigned_to",
        "parent",
        "supplier",
    ).prefetch_related(
        Prefetch(
            "asset_request_allocations",
            queryset=AssetRequestAllocation.objects.filter(returned_at__isnull=True).select_related(
                "item__asset_request__requester"
            ),
            to_attr="open_allocations",
        )
    )


@router.get("", response=list[AssetOut])
@paginate(Pagination)
def list_assets(
    request: AuthedRequest,
    filters: Query[AssetFilter],
    q: str | None = None,
    ordering: str | None = None,
) -> QuerySet[Asset]:
    queryset = search(filters.filter(asset_queryset()), q, SEARCH_FIELDS)
    return order(queryset, ordering, ORDERING_FIELDS)


@router.get("/{uuid:pk}", response=AssetDetailOut)
def get_asset(request: AuthedRequest, pk: UUID) -> Asset:
    return get_object_or_404(asset_queryset(), pk=pk)


@router.post("", response={201: AssetDetailOut})
def create_asset(request: AuthedRequest, payload: AssetIn) -> Status[Asset]:
    asset = asset_service.create_asset(payload.dict(), request.user)
    return Status(201, get_asset(request, asset.pk))


@router.post("/bulk", response={201: list[AssetOut]})
def bulk_create_assets(request: AuthedRequest, payload: AssetBulkIn) -> Status[list[Asset]]:
    """Create several devices of the same model from a list of scanned serial numbers."""
    data = payload.dict()
    serials = data.pop("serial_numbers")
    created = asset_service.bulk_create_assets(data, serials, request.user)
    return Status(201, list(asset_queryset().filter(pk__in=[a.pk for a in created])))


@router.get("/series/preview", response=AssetSeriesPreviewOut)
def preview_series(request: AuthedRequest, model: UUID, count: int = 1) -> asset_service.SeriesPreview:
    """The inventory numbers a series of ``count`` devices of ``model`` would get."""
    asset_model = get_object_or_404(AssetModel.objects.select_related("category", "manufacturer"), pk=model)
    return asset_service.preview_series(asset_model, count)


@router.post("/series", response={201: list[AssetOut]})
def create_series(request: AuthedRequest, payload: AssetSeriesIn) -> Status[list[Asset]]:
    """Create several identical devices of one model, numbered in a row from its sequence."""
    data = payload.dict()
    count = data.pop("count")
    created = asset_service.create_series(data, count, request.user)
    return Status(201, list(asset_queryset().filter(pk__in=[a.pk for a in created])))


@router.put("/{uuid:pk}", response=AssetDetailOut)
def update_asset(request: AuthedRequest, pk: UUID, payload: AssetIn) -> Asset:
    asset = get_object_or_404(Asset, pk=pk)
    asset_service.update_asset(asset, payload.dict(), request.user)
    return get_asset(request, pk)


@router.post("/{uuid:pk}/assign", response=AssetDetailOut)
def assign_asset(request: AuthedRequest, pk: UUID, payload: AssetAssignIn) -> Asset:
    """Hand a device to an employee directly, or take it back with ``user: null``."""
    asset = get_object_or_404(Asset, pk=pk)
    asset_service.update_asset(asset, {"assigned_to": payload.user}, request.user)
    return get_asset(request, pk)


@router.delete("/{uuid:pk}", response={204: None})
def delete_asset(request: AuthedRequest, pk: UUID) -> Status[None]:
    try:
        get_object_or_404(Asset, pk=pk).delete()
    except ProtectedError as exc:
        raise BusinessError(
            _("The device appears in requests or orders and cannot be deleted. Set it to “Retired” instead.")
        ) from exc
    return Status(204, None)

from typing import Annotated
from uuid import UUID

from django.db.models import F, Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import it_staff_auth
from apps.inventory.models import StockItem
from apps.inventory.schemas.stock import (
    StockItemIn,
    StockItemOut,
    StockItemUpdateIn,
    StockMoveIn,
    StockMovementOut,
)
from apps.inventory.services.stock import get_stock_item, move_stock

router = Router(tags=["stock"], auth=it_staff_auth)


class StockFilter(FilterSchema):
    model: Annotated[UUID | None, FilterLookup("model_id")] = None
    category: Annotated[UUID | None, FilterLookup("model__category_id")] = None
    location: Annotated[UUID | None, FilterLookup("location_id")] = None
    below_minimum: bool | None = None

    def filter_below_minimum(self, value: bool | None):
        return Q(quantity__lt=F("min_quantity")) if value else Q()


def stock_queryset():
    return StockItem.objects.select_related("model__manufacturer", "model__category", "location__parent")


@router.get("", response=list[StockItemOut])
@paginate(Pagination)
def list_stock(
    request: HttpRequest,
    filters: Query[StockFilter],
    q: str | None = None,
    ordering: str | None = None,
):
    queryset = search(
        filters.filter(stock_queryset()),
        q,
        ("model__name", "model__manufacturer__name", "model__ean", "model__part_number"),
    )
    return order(queryset, ordering, ("model__name", "location__name", "quantity"))


@router.post("", response={201: StockItemOut})
def create_stock_item(request: HttpRequest, payload: StockItemIn):
    item = get_stock_item(payload.model, payload.location)
    item.min_quantity = payload.min_quantity
    item.save()
    return Status(201, stock_queryset().get(pk=item.pk))


@router.get("/{uuid:pk}", response=StockItemOut)
def get_stock(request: HttpRequest, pk: UUID):
    return get_object_or_404(stock_queryset(), pk=pk)


@router.put("/{uuid:pk}", response=StockItemOut)
def update_stock_item(request: HttpRequest, pk: UUID, payload: StockItemUpdateIn):
    item = get_object_or_404(StockItem, pk=pk)
    item.min_quantity = payload.min_quantity
    item.save()
    return stock_queryset().get(pk=pk)


@router.get("/{uuid:pk}/movements", response=list[StockMovementOut])
def list_movements(request: HttpRequest, pk: UUID):
    return list(
        get_object_or_404(StockItem, pk=pk).movements.select_related("performed_by", "recipient").all()[:200]
    )


@router.post("/{uuid:pk}/move", response=StockItemOut)
def move(request: HttpRequest, pk: UUID, payload: StockMoveIn):
    """Book goods in or out, e.g. hand out two ink cartridges."""
    item = get_object_or_404(StockItem, pk=pk)
    move_stock(
        item,
        payload.delta,
        payload.reason,
        request.user,
        note=payload.note,
        recipient_id=payload.recipient,
    )
    return stock_queryset().get(pk=pk)

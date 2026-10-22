from typing import Annotated
from uuid import UUID

from django.db.models import Prefetch
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import permission_auth
from apps.procurement.models import PurchaseOrder, PurchaseOrderLine
from apps.procurement.schemas.purchase_order import (
    MarkOrderedIn,
    PurchaseOrderIn,
    PurchaseOrderListOut,
    PurchaseOrderOut,
    ReceiveIn,
)
from apps.procurement.services import orders as order_service

router = Router(tags=["procurement"], auth=permission_auth("procurement"))


class OrderFilter(FilterSchema):
    status: Annotated[list[str] | None, FilterLookup("status__in")] = None
    supplier: Annotated[UUID | None, FilterLookup("supplier_id")] = None
    asset_request: Annotated[UUID | None, FilterLookup("lines__asset_request_item__asset_request_id")] = None


def order_queryset():
    lines = PurchaseOrderLine.objects.select_related(
        "asset_model__manufacturer",
        "asset_request_item__asset_request__requester",
        "asset_request_item__category",
        "asset_request_item__asset_model__manufacturer",
    )
    return PurchaseOrder.objects.select_related(
        "supplier", "delivery_location__parent", "created_by"
    ).prefetch_related(Prefetch("lines", queryset=lines))


@router.get("", response=list[PurchaseOrderListOut])
@paginate(Pagination)
def list_orders(
    request: HttpRequest,
    filters: Query[OrderFilter],
    q: str | None = None,
    ordering: str | None = None,
):
    queryset = search(
        filters.filter(order_queryset()).distinct(),
        q,
        (
            "number",
            "supplier__name",
            "supplier_reference",
            "lines__description",
            "lines__asset_model__name",
        ),
    )
    return order(queryset, ordering, ("number", "created_at", "order_date", "expected_date", "status"))


@router.get("/{uuid:pk}", response=PurchaseOrderOut)
def get_order(request: HttpRequest, pk: UUID):
    return get_object_or_404(order_queryset(), pk=pk)


@router.post("", response={201: PurchaseOrderOut})
def create_order(request: HttpRequest, payload: PurchaseOrderIn):
    data = payload.dict(exclude={"lines"})
    lines = [line.dict() for line in payload.lines or []]
    purchase_order = order_service.create_order(data, lines, request.user)
    return Status(201, get_order(request, purchase_order.pk))


@router.put("/{uuid:pk}", response=PurchaseOrderOut)
def update_order(request: HttpRequest, pk: UUID, payload: PurchaseOrderIn):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    lines = [line.dict() for line in payload.lines] if payload.lines is not None else None
    order_service.update_order(purchase_order, payload.dict(exclude={"lines"}), lines)
    return get_order(request, pk)


@router.post("/{uuid:pk}/ordered", response=PurchaseOrderOut)
def mark_ordered(request: HttpRequest, pk: UUID, payload: MarkOrderedIn):
    order_service.mark_ordered(
        get_object_or_404(PurchaseOrder, pk=pk),
        payload.order_date,
        payload.expected_date,
        payload.supplier_reference,
    )
    return get_order(request, pk)


@router.post("/{uuid:pk}/receive", response=PurchaseOrderOut)
def receive(request: HttpRequest, pk: UUID, payload: ReceiveIn):
    receipts = [receipt.dict() for receipt in payload.receipts]
    order_service.receive(get_object_or_404(PurchaseOrder, pk=pk), receipts, request.user)
    return get_order(request, pk)


@router.post("/{uuid:pk}/cancel", response=PurchaseOrderOut)
def cancel(request: HttpRequest, pk: UUID):
    order_service.cancel(get_object_or_404(PurchaseOrder, pk=pk))
    return get_order(request, pk)


@router.delete("/{uuid:pk}", response={204: None})
def delete_order(request: HttpRequest, pk: UUID):
    get_object_or_404(PurchaseOrder, pk=pk, status=PurchaseOrder.Status.DRAFT).delete()
    return Status(204, None)

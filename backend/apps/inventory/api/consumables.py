from typing import Annotated
from uuid import UUID

from django.db.models import F, Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import permission_auth
from apps.inventory.models import Consumable
from apps.inventory.schemas.consumable import (
    ConsumableIn,
    ConsumableMoveIn,
    ConsumableMovementOut,
    ConsumableOut,
    ConsumableUpdateIn,
)
from apps.inventory.services.consumables import get_consumable, move_consumable

router = Router(tags=["consumables"], auth=permission_auth("consumables"))


class ConsumableFilter(FilterSchema):
    model: Annotated[UUID | None, FilterLookup("model_id")] = None
    category: Annotated[UUID | None, FilterLookup("model__category_id")] = None
    location: Annotated[UUID | None, FilterLookup("location_id")] = None
    below_minimum: bool | None = None

    def filter_below_minimum(self, value: bool | None):
        return Q(quantity__lt=F("min_quantity")) if value else Q()


def consumable_queryset():
    return Consumable.objects.select_related("model__manufacturer", "model__category", "location__parent")


@router.get("", response=list[ConsumableOut])
@paginate(Pagination)
def list_consumables(
    request: HttpRequest,
    filters: Query[ConsumableFilter],
    q: str | None = None,
    ordering: str | None = None,
):
    queryset = search(
        filters.filter(consumable_queryset()),
        q,
        (
            "model__name",
            "model__designation",
            "model__manufacturer__name",
            "model__ean",
            "model__part_number",
        ),
    )
    return order(queryset, ordering, ("model__name", "location__name", "quantity"))


@router.post("", response={201: ConsumableOut})
def create_consumable(request: HttpRequest, payload: ConsumableIn):
    item = get_consumable(payload.model, payload.location)
    item.min_quantity = payload.min_quantity
    item.save()
    return Status(201, consumable_queryset().get(pk=item.pk))


@router.get("/{uuid:pk}", response=ConsumableOut)
def get_consumable_detail(request: HttpRequest, pk: UUID):
    return get_object_or_404(consumable_queryset(), pk=pk)


@router.put("/{uuid:pk}", response=ConsumableOut)
def update_consumable(request: HttpRequest, pk: UUID, payload: ConsumableUpdateIn):
    item = get_object_or_404(Consumable, pk=pk)
    item.min_quantity = payload.min_quantity
    item.save()
    return consumable_queryset().get(pk=pk)


@router.get("/{uuid:pk}/movements", response=list[ConsumableMovementOut])
def list_movements(request: HttpRequest, pk: UUID):
    return list(
        get_object_or_404(Consumable, pk=pk).movements.select_related("performed_by", "recipient").all()[:200]
    )


@router.post("/{uuid:pk}/move", response=ConsumableOut)
def move(request: HttpRequest, pk: UUID, payload: ConsumableMoveIn):
    """Book goods in or out, e.g. hand out two ink cartridges."""
    item = get_object_or_404(Consumable, pk=pk)
    move_consumable(
        item,
        payload.delta,
        payload.reason,
        request.user,
        note=payload.note,
        recipient_id=payload.recipient,
    )
    return consumable_queryset().get(pk=pk)

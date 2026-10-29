from datetime import date
from typing import Annotated
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import search
from apps.core.api.security import AuthedRequest, permission_auth
from apps.inventory.models import Asset, AssetEvent
from apps.inventory.schemas.asset_event import AssetEventIn, AssetEventOut, AssetEventWithAssetOut
from apps.inventory.services import assets as asset_service

router = Router(tags=["asset events"], auth=permission_auth("assets"))


class EventFilter(FilterSchema):
    kind: Annotated[list[str] | None, FilterLookup("kind__in")] = None
    model: Annotated[UUID | None, FilterLookup("asset__model_id")] = None
    category: Annotated[UUID | None, FilterLookup("asset__model__category_id")] = None
    since: Annotated[date | None, FilterLookup("occurred_at__date__gte")] = None
    until: Annotated[date | None, FilterLookup("occurred_at__date__lte")] = None


def event_queryset():
    return AssetEvent.objects.select_related(
        "performed_by", "related_user", "asset_request", "asset__model__manufacturer"
    )


@router.get("/events", response=list[AssetEventWithAssetOut])
@paginate(Pagination)
def list_events(request: AuthedRequest, filters: Query[EventFilter], q: str | None = None):
    """Life cycle log across all devices, e.g. every battery replacement in 2026."""
    queryset = filters.filter(event_queryset())
    return search(
        queryset, q, ("asset__inventory_number", "asset__serial_number", "description", "component")
    )


@router.get("/assets/{uuid:pk}/events", response=list[AssetEventOut])
def list_asset_events(request: AuthedRequest, pk: UUID):
    return list(event_queryset().filter(asset_id=pk))


@router.post("/assets/{uuid:pk}/events", response={201: AssetEventOut})
def create_asset_event(request: AuthedRequest, pk: UUID, payload: AssetEventIn):
    asset = get_object_or_404(Asset, pk=pk)
    data = payload.dict(exclude={"consume"})
    event = asset_service.record_event(
        asset, data, request.user, payload.consume.dict() if payload.consume else None
    )
    return Status(201, event_queryset().get(pk=event.pk))


@router.delete("/events/{uuid:pk}", response={204: None})
def delete_event(request: AuthedRequest, pk: UUID):
    get_object_or_404(AssetEvent, pk=pk, kind__in=AssetEvent.MANUAL_KINDS).delete()
    return Status(204, None)

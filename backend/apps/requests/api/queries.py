from uuid import UUID

from django.db.models import Prefetch, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import can
from apps.requests.models import (
    AssetRequest,
    AssetRequestAllocation,
    AssetRequestEvent,
    AssetRequestItem,
    DeviceReturn,
)


def asset_request_queryset() -> QuerySet[AssetRequest]:
    allocations = AssetRequestAllocation.objects.select_related(
        # The category gives each allocation its icon.
        "asset__model__manufacturer",
        "asset__model__category",
        "consumable__model__manufacturer",
        "consumable__model__category",
        "consumable__location__parent",
        "license__model__manufacturer",
        "license__model__category",
        "license_assignment__asset__model__manufacturer",
        "allocated_by",
    )
    items = (
        AssetRequestItem.objects.select_related(
            "category", "asset_model__manufacturer", "asset_model__category"
        )
        .annotate(_quantity_allocated=Coalesce(Sum("allocations__quantity"), 0))
        # Aggregating queries ignore Meta.ordering, so keep the requested order explicitly.
        .order_by("position")
        .prefetch_related(Prefetch("allocations", queryset=allocations))
    )
    return AssetRequest.objects.select_related(
        "requester__department",
        "created_by",
        "handled_by",
        "prepared_by",
        "assigned_team",
        "assignee",
        "approver",
        "pickup_location__parent",
        "follows",
        "handover__received_by",
        "handover__handed_out_by",
        "handover__recorded_by",
    ).prefetch_related(
        Prefetch("items", queryset=items),
        Prefetch("returns", queryset=DeviceReturn.objects.select_related("returned_by")),
        Prefetch("events", queryset=AssetRequestEvent.objects.select_related("actor")),
    )


def visible_asset_requests(request: HttpRequest) -> QuerySet[AssetRequest]:
    queryset = asset_request_queryset()
    if can(request.user, "requests"):
        return queryset
    return queryset.filter(requester=request.user)


def approvable_asset_requests(user) -> QuerySet[AssetRequest]:
    """Requests that went to one of the departments ``user`` approves for."""
    return (
        asset_request_queryset()
        .filter(requester__department__approvers=user)
        .exclude(approval=AssetRequest.Approval.NOT_REQUIRED)
    )


def get_asset_request(request: HttpRequest, pk: UUID, *, as_approver: bool = False) -> AssetRequest:
    """A request the user may see; ``as_approver`` adds those they decide on."""
    asset_request = visible_asset_requests(request).filter(pk=pk).first()
    if asset_request is None and as_approver:
        asset_request = approvable_asset_requests(request.user).filter(pk=pk).first()
    if asset_request is None:
        raise Http404
    return asset_request


def get_for_update(pk: UUID) -> AssetRequest:
    """Locked plain instance for workflow transitions (no prefetch caches that could go stale).

    The row lock makes concurrent transitions (e.g. signing twice) wait and then see
    the new status; callers must run inside ``transaction.atomic``.
    """
    return get_object_or_404(AssetRequest.objects.select_for_update(), pk=pk)

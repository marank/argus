"""Endpoints for the employee self-service portal."""

from datetime import date, timedelta
from typing import TypedDict
from uuid import UUID

from django.db.models import Prefetch, Q, QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router, Status

from apps.accounts.models import User
from apps.accounts.permissions import ResourceKey, can
from apps.core.api.security import AuthedRequest, permission_auth
from apps.core.features import FeatureKey, is_enabled
from apps.core.models import SiteSettings
from apps.inventory.api.issues import issue_detail
from apps.inventory.models import Asset, AssetIssue, AssetIssueStatus, LicenseAssignment
from apps.inventory.schemas.asset_issue import (
    AssetIssueDetailOut,
    AssetIssueIn,
    IssueMessageIn,
    OwnIssueOut,
    OwnIssueWithDeviceOut,
)
from apps.inventory.schemas.license import OwnLicenseOut
from apps.inventory.services.availability import Counts, period_availability
from apps.inventory.services.issues import (
    mark_seen,
    post_message,
    report_issue,
    update_issue,
    with_messages,
)
from apps.masterdata.models import AssetModel, Category, CategoryKind
from apps.requests.api.queries import approvable_asset_requests
from apps.requests.models import AssetRequest, AssetRequestAllocation, AssetRequestStatus
from apps.requests.schemas.catalog import (
    AvailabilityOut,
    CatalogCategoryOut,
    MenuCountsOut,
    MyAssetOut,
    MyConsumablesOut,
)

router = Router(tags=["portal"])


class Availability(TypedDict):
    """Serialized as ``AvailabilityOut``."""

    models: dict[str, dict[str, int]]
    categories: dict[str, dict[str, int]]


class DeviceConsumables(TypedDict):
    """Serialized as ``MyConsumablesOut``."""

    asset: Asset
    consumables: list[AssetModel]


class OwnAsset(TypedDict):
    """Serialized as ``MyAssetOut``."""

    id: UUID
    inventory_number: str
    serial_number: str
    model: AssetModel
    category: str
    category_icon: str
    assigned_since: str | None
    asset_request_number: str | None
    return_due: str | None
    issues: list[AssetIssue]


class MenuCounts(TypedDict):
    """Serialized as ``MenuCountsOut``."""

    requests: int
    approvals: int
    issues: int
    issues_updated: bool


def _period(start: date | None, end: date | None, permanent: bool) -> tuple[date, date | None]:
    """The requested period; without dates the default loan period from today."""
    start = start or timezone.localdate()
    if permanent:
        return start, None
    return start, end or start + timedelta(days=SiteSettings.load().default_loan_days - 1)


def _set_counts(target: AssetModel | Category, counts: Counts | None) -> None:
    target.available = counts.available if counts else None
    target.reserved = counts.reserved if counts else None


def _accessory_category_ids() -> set[UUID]:
    """Categories marked as accessories and all categories below them."""
    rows = list(Category.objects.values_list("pk", "parent_id", "is_accessory"))
    children: dict[UUID, list[UUID]] = {}
    for pk, parent_id, _ in rows:
        # Top-level categories have no parent; the stubs type values_list() columns as set.
        if parent_id is not None:  # type: ignore[comparison-overlap]
            children.setdefault(parent_id, []).append(pk)
    ids: set[UUID] = set()
    frontier = [pk for pk, _, is_accessory in rows if is_accessory]
    while frontier:
        ids.update(frontier)
        frontier = [child for pk in frontier for child in children.get(pk, []) if child not in ids]
    return ids


@router.get("/catalog", response=list[CatalogCategoryOut])
def catalog(
    request: AuthedRequest, start: date | None = None, end: date | None = None, permanent: bool = False
) -> list[Category]:
    """Requestable categories with their models.

    Availability for the period is only included for IT staff who handle requests; employees request
    what they need and IT decides what the pool can cover.
    """
    show_availability = can(request.user, ResourceKey.REQUESTS)
    model_counts, category_counts = (
        period_availability(*_period(start, end, permanent)) if show_availability else ({}, {})
    )
    categories = Category.objects.filter(is_requestable=True)
    models = AssetModel.objects.filter(is_requestable=True, is_active=True)
    if not is_enabled(FeatureKey.SOFTWARE_REQUESTS):
        # Software can be switched off as a request option in the site settings.
        categories = categories.exclude(kind=CategoryKind.SOFTWARE)
        models = models.exclude(tracking=AssetModel.Tracking.LICENSE)
    accessory_categories = _accessory_category_ids()
    offered = {model.pk: model for model in models.select_related("manufacturer")}
    compatible: dict[UUID, set[UUID]] = {}
    for model_id, other_id in AssetModel.compatible_with.through.objects.filter(
        from_assetmodel_id__in=offered
    ).values_list("from_assetmodel_id", "to_assetmodel_id"):
        compatible.setdefault(model_id, set()).add(other_id)

    models_by_category: dict[UUID, list[AssetModel]] = {}
    for model in offered.values():
        _set_counts(model, model_counts.get(model.pk, Counts()) if show_availability else None)
        # The link is mutual; the accessory categories say which side is the accessory.
        fitting = (
            []
            if model.category_id in accessory_categories
            else [
                offered[pk]
                for pk in compatible.get(model.pk, set())
                if pk in offered and offered[pk].category_id in accessory_categories
            ]
        )
        model.accessories = [m.pk for m in sorted(fitting, key=lambda m: m.full_name.lower())]
        models_by_category.setdefault(model.category_id, []).append(model)

    result: list[Category] = []
    for category in categories:
        _set_counts(category, category_counts.get(category.pk, Counts()) if show_availability else None)
        category.in_accessory_tree = category.pk in accessory_categories
        category.models = models_by_category.get(category.pk, [])
        result.append(category)
    return result


@router.get("/availability", response=AvailabilityOut, auth=permission_auth(ResourceKey.REQUESTS))
def availability(
    request: AuthedRequest, start: date, end: date | None = None, permanent: bool = False
) -> Availability:
    """Counts of all models and categories for a period; the request form refreshes with it."""
    model_counts, category_counts = period_availability(*_period(start, end, permanent))
    return {
        "models": {str(k): vars(v) for k, v in model_counts.items()},
        "categories": {str(k): vars(v) for k, v in category_counts.items()},
    }


@router.get("/my-consumables", response=list[MyConsumablesOut])
def my_consumables(request: AuthedRequest) -> list[DeviceConsumables]:
    """Requestable consumables that fit the employee's devices, grouped by device.

    A consumable fits when it is assigned to the device itself or marked as
    compatible with the device's model.
    """
    assets = list(
        Asset.objects.filter(assigned_to=request.user)
        .select_related("model__manufacturer")
        .order_by("inventory_number")
    )
    # What fits which device, in two queries for all devices (see Asset.consumable_models).
    own: dict[UUID, set[UUID]] = {}
    for asset_id, model_id in Asset.consumables.through.objects.filter(asset__in=assets).values_list(
        "asset_id", "assetmodel_id"
    ):
        own.setdefault(asset_id, set()).add(model_id)
    compatible: dict[UUID, set[UUID]] = {}
    for model_id, other_id in AssetModel.compatible_with.through.objects.filter(
        from_assetmodel_id__in={asset.model_id for asset in assets}
    ).values_list("from_assetmodel_id", "to_assetmodel_id"):
        compatible.setdefault(model_id, set()).add(other_id)
    offered = {
        model.pk: model
        for model in AssetModel.objects.filter(
            pk__in=set().union(*own.values(), *compatible.values()),
            tracking=AssetModel.Tracking.BULK,
            is_requestable=True,
            is_active=True,
        ).select_related("manufacturer")
    }
    result: list[DeviceConsumables] = []
    for asset in assets:
        ids = own.get(asset.pk, set()) | compatible.get(asset.model_id, set())
        consumables = sorted(
            (offered[pk] for pk in ids if pk in offered), key=lambda m: (m.manufacturer.name, m.name)
        )
        if consumables:
            result.append({"asset": asset, "consumables": consumables})
    return result


def _own_assets(user: User, assets: QuerySet[Asset], issues: QuerySet[AssetIssue]) -> list[OwnAsset]:
    """Devices of the employee with their open request and the given reports."""
    assets = assets.filter(assigned_to=user).select_related("model__manufacturer", "model__category")
    assets = assets.prefetch_related(
        Prefetch("issues", queryset=with_messages(issues), to_attr="visible_issues")
    )
    allocations = {
        a.asset_id: a.item.asset_request
        for a in AssetRequestAllocation.objects.filter(
            asset__in=assets, returned_at__isnull=True
        ).select_related("item__asset_request")
    }
    result: list[OwnAsset] = []
    for asset in assets:
        asset_request = allocations.get(asset.pk)
        result.append(
            {
                "id": asset.pk,
                "inventory_number": asset.inventory_number,
                "serial_number": asset.serial_number,
                "model": asset.model,
                "category": asset.model.category.name,
                "category_icon": asset.model.category.icon,
                "assigned_since": asset.assigned_since.isoformat() if asset.assigned_since else None,
                "asset_request_number": asset_request.number if asset_request else None,
                "return_due": (
                    asset_request.end_date.isoformat() if asset_request and asset_request.end_date else None
                ),
                "issues": asset.visible_issues,
            }
        )
    return result


@router.get("/my-assets", response=list[MyAssetOut])
def my_assets(request: AuthedRequest) -> list[OwnAsset]:
    """Devices currently handed out to the logged-in employee."""
    # Open reports, plus resolved ones of the last 14 days so the answer stays visible.
    recent = timezone.now() - timedelta(days=14)
    issues = AssetIssue.objects.filter(Q(resolved_at__isnull=True) | Q(resolved_at__gte=recent))
    return _own_assets(request.user, Asset.objects.all(), issues)


@router.get("/my-assets/{uuid:pk}", response=MyAssetOut)
def my_asset(request: AuthedRequest, pk: UUID) -> OwnAsset:
    """One of the employee's devices with all its problem reports."""
    devices = _own_assets(request.user, Asset.objects.filter(pk=pk), AssetIssue.objects.all())
    if not devices:
        raise Http404
    return devices[0]


@router.post("/my-assets/{uuid:pk}/issues", response={201: OwnIssueOut})
def report(request: AuthedRequest, pk: UUID, payload: AssetIssueIn) -> Status[AssetIssue]:
    """Report a problem with one of the employee's own devices; IT sees it under problem reports."""
    asset = get_object_or_404(Asset, pk=pk, assigned_to=request.user)
    return Status(201, report_issue(asset, request.user, payload.kind, payload.description))


@router.get("/my-issues", response=list[OwnIssueWithDeviceOut])
def my_issues(request: AuthedRequest) -> QuerySet[AssetIssue]:
    """All problems the employee has reported, newest first."""
    issues = with_messages(
        AssetIssue.objects.filter(reported_by=request.user).select_related(
            "asset__model__manufacturer", "asset__model__category"
        )
    )
    for issue in issues:
        issue.still_assigned = issue.asset.assigned_to_id == request.user.pk
    return issues


def _own_issues(request: AuthedRequest) -> QuerySet[AssetIssue]:
    return AssetIssue.objects.filter(reported_by=request.user)


@router.get("/my-issues/{uuid:pk}", response=AssetIssueDetailOut)
def my_issue(request: AuthedRequest, pk: UUID) -> AssetIssue:
    """One of the employee's reports with its conversation; opening it marks IT's updates seen."""
    issue = issue_detail(_own_issues(request), pk)
    mark_seen(request.user, issue)
    return issue


@router.post("/my-issues/{uuid:pk}/messages", response=AssetIssueDetailOut)
def my_issue_message(request: AuthedRequest, pk: UUID, payload: IssueMessageIn) -> AssetIssue:
    post_message(get_object_or_404(_own_issues(request), pk=pk), request.user, payload.text, by_it=False)
    return issue_detail(_own_issues(request), pk)


@router.post("/my-issues/{uuid:pk}/resolve", response=AssetIssueDetailOut)
def my_issue_resolve(request: AuthedRequest, pk: UUID, payload: IssueMessageIn) -> AssetIssue:
    """The employee marks the problem resolved, optionally saying how."""
    issue = get_object_or_404(_own_issues(request), pk=pk)
    update_issue(issue, request.user, AssetIssueStatus.RESOLVED, payload.text, by_it=False)
    return issue_detail(_own_issues(request), pk)


@router.get("/menu-counts", response=MenuCountsOut)
def menu_counts(request: AuthedRequest) -> MenuCounts:
    """Open requests, approvals and problem reports of the user, for the badges in the menu.

    Approvals always wait for the user; reports only when IT changed one since the user last opened it.
    """
    approvals = approvable_asset_requests(request.user).filter(status=AssetRequestStatus.PENDING_APPROVAL)
    issues = AssetIssue.objects.filter(reported_by=request.user)
    return {
        "requests": AssetRequest.objects.filter(
            requester=request.user, status__in=AssetRequest.OPEN_STATUSES
        ).count(),
        "approvals": approvals.count(),
        "issues": issues.exclude(status=AssetIssueStatus.RESOLVED).count(),
        "issues_updated": issues.filter(unseen_update=True).exists(),
    }


@router.get("/my-licenses", response=list[OwnLicenseOut])
def my_licenses(request: AuthedRequest) -> list[LicenseAssignment]:
    """Software the employee uses: seats assigned to them or to one of their devices."""
    return list(
        LicenseAssignment.objects.filter(Q(user=request.user) | Q(asset__assigned_to=request.user))
        .select_related(
            "license__model__manufacturer", "license__model__category", "asset__model__manufacturer"
        )
        .order_by("license__model__name")
    )

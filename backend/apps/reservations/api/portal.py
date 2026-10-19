"""Endpoints for the employee self-service portal."""

from datetime import date, timedelta
from uuid import UUID

from django.db.models import Prefetch, Q
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router, Status

from apps.core.api.security import is_it_staff, it_staff_auth
from apps.core.features import is_enabled
from apps.core.models import SiteSettings
from apps.inventory.models import Asset, AssetIssue, LicenseAssignment
from apps.inventory.schemas.asset_issue import AssetIssueIn, OwnIssueOut, OwnIssueWithDeviceOut
from apps.inventory.schemas.license import OwnLicenseOut
from apps.inventory.services.availability import Counts, period_availability
from apps.inventory.services.issues import report_issue
from apps.masterdata.models import AssetModel, Category
from apps.reservations.models import ReservationAllocation
from apps.reservations.schemas.catalog import (
    AvailabilityOut,
    CatalogCategoryOut,
    MyAssetOut,
    MyConsumablesOut,
)

router = Router(tags=["portal"])


def _period(start: date | None, end: date | None, permanent: bool) -> tuple[date, date | None]:
    """The requested period; without dates the default loan period from today."""
    start = start or timezone.localdate()
    if permanent:
        return start, None
    return start, end or start + timedelta(days=SiteSettings.load().default_loan_days - 1)


def _set_counts(target, counts: Counts | None) -> None:
    target.available = counts.available if counts else None
    target.reserved = counts.reserved if counts else None


@router.get("/catalog", response=list[CatalogCategoryOut])
def catalog(
    request: HttpRequest, start: date | None = None, end: date | None = None, permanent: bool = False
):
    """Requestable categories with their models.

    Availability for the period is only included for IT staff; employees request
    what they need and IT decides what the pool can cover.
    """
    show_availability = is_it_staff(request.user)
    model_counts, category_counts = (
        period_availability(*_period(start, end, permanent)) if show_availability else ({}, {})
    )
    categories = Category.objects.filter(is_requestable=True)
    models = AssetModel.objects.filter(is_requestable=True, is_active=True)
    if not is_enabled("software_requests"):
        # Software can be switched off as a request option in the site settings.
        categories = categories.exclude(kind=Category.Kind.SOFTWARE)
        models = models.exclude(tracking=AssetModel.Tracking.LICENSE)
    models_by_category: dict[UUID, list] = {}
    for model in models.select_related("manufacturer"):
        _set_counts(model, model_counts.get(model.pk, Counts()) if show_availability else None)
        models_by_category.setdefault(model.category_id, []).append(model)

    result = []
    for category in categories:
        _set_counts(category, category_counts.get(category.pk, Counts()) if show_availability else None)
        category.models = models_by_category.get(category.pk, [])
        result.append(category)
    return result


@router.get("/availability", response=AvailabilityOut, auth=it_staff_auth)
def availability(request: HttpRequest, start: date, end: date | None = None, permanent: bool = False):
    """Counts of all models and categories for a period; the request form refreshes with it."""
    model_counts, category_counts = period_availability(*_period(start, end, permanent))
    return {
        "models": {str(k): vars(v) for k, v in model_counts.items()},
        "categories": {str(k): vars(v) for k, v in category_counts.items()},
    }


@router.get("/my-consumables", response=list[MyConsumablesOut])
def my_consumables(request: HttpRequest):
    """Requestable consumables that fit the employee's devices, grouped by device.

    A consumable fits when it is assigned to the device itself or marked as
    compatible with the device's model.
    """
    result = []
    assets = Asset.objects.filter(assigned_to=request.user).select_related("model__manufacturer")
    for asset in assets.order_by("inventory_number"):
        consumables = list(
            asset.consumable_models()
            .filter(is_requestable=True, is_active=True)
            .select_related("manufacturer")
            .order_by("manufacturer__name", "name")
        )
        if consumables:
            result.append({"asset": asset, "consumables": consumables})
    return result


def _own_assets(user, assets, issues) -> list[dict]:
    """Devices of the employee with their open reservation and the given reports."""
    assets = assets.filter(assigned_to=user).select_related("model__manufacturer", "model__category")
    assets = assets.prefetch_related(Prefetch("issues", queryset=issues, to_attr="visible_issues"))
    allocations = {
        a.asset_id: a.item.reservation
        for a in ReservationAllocation.objects.filter(
            asset__in=assets, returned_at__isnull=True
        ).select_related("item__reservation")
    }
    result = []
    for asset in assets:
        reservation = allocations.get(asset.pk)
        result.append(
            {
                "id": asset.pk,
                "inventory_number": asset.inventory_number,
                "serial_number": asset.serial_number,
                "model": asset.model,
                "category": asset.model.category.name,
                "category_icon": asset.model.category.icon,
                "assigned_since": asset.assigned_since.isoformat() if asset.assigned_since else None,
                "reservation_number": reservation.number if reservation else None,
                "return_due": (
                    reservation.end_date.isoformat() if reservation and reservation.end_date else None
                ),
                "issues": asset.visible_issues,
            }
        )
    return result


@router.get("/my-assets", response=list[MyAssetOut])
def my_assets(request: HttpRequest):
    """Devices currently handed out to the logged-in employee."""
    # Open reports, plus resolved ones of the last 14 days so the answer stays visible.
    recent = timezone.now() - timedelta(days=14)
    issues = AssetIssue.objects.filter(Q(resolved_at__isnull=True) | Q(resolved_at__gte=recent))
    return _own_assets(request.user, Asset.objects.all(), issues)


@router.get("/my-assets/{uuid:pk}", response=MyAssetOut)
def my_asset(request: HttpRequest, pk: UUID):
    """One of the employee's devices with all its problem reports."""
    devices = _own_assets(request.user, Asset.objects.filter(pk=pk), AssetIssue.objects.all())
    if not devices:
        raise Http404
    return devices[0]


@router.post("/my-assets/{uuid:pk}/issues", response={201: OwnIssueOut})
def report(request: HttpRequest, pk: UUID, payload: AssetIssueIn):
    """Report a problem with one of the employee's own devices; IT sees it under problem reports."""
    asset = get_object_or_404(Asset, pk=pk, assigned_to=request.user)
    return Status(201, report_issue(asset, request.user, payload.kind, payload.description))


@router.get("/my-issues", response=list[OwnIssueWithDeviceOut])
def my_issues(request: HttpRequest):
    """All problems the employee has reported, newest first."""
    issues = AssetIssue.objects.filter(reported_by=request.user).select_related(
        "asset__model__manufacturer", "asset__model__category"
    )
    for issue in issues:
        issue.still_assigned = issue.asset.assigned_to_id == request.user.pk
    return issues


@router.get("/my-licenses", response=list[OwnLicenseOut])
def my_licenses(request: HttpRequest):
    """Software the employee uses: seats assigned to them or to one of their devices."""
    return list(
        LicenseAssignment.objects.filter(Q(user=request.user) | Q(asset__assigned_to=request.user))
        .select_related(
            "license__model__manufacturer", "license__model__category", "asset__model__manufacturer"
        )
        .order_by("license__model__name")
    )

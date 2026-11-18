"""Writing the activity log: one row per step of IT's daily work."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.db.models import QuerySet

from apps.accounts.permissions import ResourceKey, can
from apps.activity.models import Activity, ActivityArea, ActivityKind

if TYPE_CHECKING:
    from apps.accounts.models import User
    from apps.inventory.models import Asset, AssetIssue, Consumable, License
    from apps.procurement.models import PurchaseOrder
    from apps.requests.models import AssetRequest

AREA_BY_PREFIX = {
    "request_": ActivityArea.REQUESTS,
    "asset_": ActivityArea.ASSETS,
    "assets_": ActivityArea.ASSETS,
    "issue_": ActivityArea.ISSUES,
    "consumable_": ActivityArea.CONSUMABLES,
    "license_": ActivityArea.LICENSES,
    "order_": ActivityArea.PROCUREMENT,
}

_muted: ContextVar[bool] = ContextVar("activity_muted", default=False)


def area_of(kind: str) -> ActivityArea:
    return next(area for prefix, area in AREA_BY_PREFIX.items() if kind.startswith(prefix))


@contextmanager
def muted() -> Iterator[None]:
    """Writes nothing inside: the caller records the whole step as one row instead."""
    token = _muted.set(True)
    try:
        yield
    finally:
        _muted.reset(token)


def log(
    kind: ActivityKind,
    subject_id: UUID | None,
    label: str,
    user: User | None = None,
    *,
    related_user: User | None = None,
    related_user_id: Any = None,
    quantity: int | None = None,
    detail: str = "",
) -> Activity | None:
    if _muted.get():
        return None
    return Activity.objects.create(
        area=area_of(kind),
        kind=kind,
        subject_id=subject_id,
        subject_label=label[:300],
        actor=user if getattr(user, "pk", None) else None,
        related_user_id=related_user.pk if related_user else related_user_id,
        quantity=quantity,
        detail=detail.strip(),
    )


def visible(user: User) -> QuerySet[Activity]:
    """The rows of the areas ``user`` may read."""
    areas = [area for area in ActivityArea if can(user, ResourceKey(area.value))]
    return Activity.objects.filter(area__in=areas).select_related("actor", "related_user")


def request_label(asset_request: AssetRequest) -> str:
    return f"{asset_request.number} – {asset_request.title}"


def asset_label(asset: Asset) -> str:
    return f"{asset.inventory_number} · {asset.model.full_name}"


def issue_label(issue: AssetIssue) -> str:
    return asset_label(issue.asset)


def consumable_label(consumable: Consumable) -> str:
    return f"{consumable.model.full_name} · {consumable.location.name}"


def license_label(license: License) -> str:
    return str(license)


def order_label(order: PurchaseOrder) -> str:
    supplier = order.supplier.name if order.supplier else ""
    return f"{order.number} · {supplier}" if supplier else order.number

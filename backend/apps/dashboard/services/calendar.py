"""Calendar feed for IT: lending periods, pickups, returns, deliveries, warranty and license ends.

Permanent hand-outs (work equipment) are left out entirely: they have no end and
would only clutter the calendar. Their pickup appointment is still shown while
the request is being prepared, because that is a date IT has to keep.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.inventory.models import Asset, License
from apps.procurement.models import PurchaseOrder
from apps.requests.models import AssetRequest

KINDS = ("loan", "pickup", "return", "delivery", "warranty", "license")


@dataclass
class Entry:
    id: str
    kind: str
    title: str
    start: date | datetime
    end: date | None = None  # exclusive, for multi-day entries
    all_day: bool = True
    status: str = ""
    overdue: bool = False
    due: date | None = None
    link: dict = field(default_factory=dict)
    details: list[str] = field(default_factory=list)


def _requester(asset_request: AssetRequest) -> str:
    return asset_request.requester.display_name


def calendar_entries(
    start: date, end: date, kinds: set[str] | None = None, asset_request_filter: Q | None = None
) -> list[Entry]:
    """Entries overlapping [start, end] (inclusive).

    ``asset_request_filter`` narrows the request entries (loans, pickups, returns),
    e.g. to the user's own; deliveries and warranty or license ends stay.
    """
    kinds = kinds or set(KINDS)
    today = timezone.localdate()
    entries: list[Entry] = []

    asset_requests = (
        AssetRequest.objects.filter(asset_request_filter or Q())
        .select_related("requester")
        .prefetch_related("items__category", "items__asset_model__manufacturer")
    )
    temporary = asset_requests.filter(
        duration=AssetRequest.Duration.TEMPORARY, status__in=AssetRequest.OPEN_STATUSES
    )

    if "loan" in kinds:
        for r in temporary.filter(start_date__lte=end, end_date__gte=start):
            items = [f"{i.quantity_target}× {i.label}" for i in r.items.all()]
            entries.append(
                Entry(
                    id=f"loan-{r.pk}",
                    kind="loan",
                    title=f"{_requester(r)} · {r.title}",
                    start=r.start_date,
                    end=r.end_date + timedelta(days=1),
                    status=r.status,
                    overdue=r.is_overdue,
                    link={"name": "request", "id": str(r.pk)},
                    details=[r.number, *items],
                )
            )

    if "pickup" in kinds:
        pickups = asset_requests.filter(
            status__in=(AssetRequest.Status.CONFIRMED, AssetRequest.Status.READY),
            pickup_at__date__gte=start,
            pickup_at__date__lte=end,
        )
        for r in pickups:
            entries.append(
                Entry(
                    id=f"pickup-{r.pk}",
                    kind="pickup",
                    title=_requester(r),
                    start=timezone.localtime(r.pickup_at),
                    all_day=False,
                    status=r.status,
                    link={"name": "request", "id": str(r.pk)},
                    details=[r.number, r.title],
                )
            )

    if "return" in kinds:
        # Overdue returns move along on today until the devices are back.
        for r in temporary.filter(status=AssetRequest.Status.HANDED_OUT, end_date__lte=end):
            overdue = r.end_date < today
            day = today if overdue else r.end_date
            if not start <= day <= end:
                continue
            entries.append(
                Entry(
                    id=f"return-{r.pk}",
                    kind="return",
                    title=_requester(r),
                    start=day,
                    due=r.end_date,
                    status=r.status,
                    overdue=overdue,
                    link={"name": "request", "id": str(r.pk)},
                    details=[r.number, r.title],
                )
            )

    if "delivery" in kinds:
        orders = PurchaseOrder.objects.select_related("supplier").filter(
            status__in=(PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED),
            expected_date__gte=start,
            expected_date__lte=end,
        )
        for o in orders:
            entries.append(
                Entry(
                    id=f"delivery-{o.pk}",
                    kind="delivery",
                    title=o.supplier.name if o.supplier else o.number,
                    start=o.expected_date,
                    status=o.status,
                    link={"name": "order", "id": str(o.pk)},
                    details=[o.number, *(f"{line.quantity_open}× {line.label}" for line in o.lines.all())],
                )
            )

    if "warranty" in kinds:
        assets = (
            Asset.objects.select_related("model__manufacturer")
            .filter(warranty_until__gte=start, warranty_until__lte=end)
            .exclude(status__in=(Asset.Status.RETIRED, Asset.Status.LOST))
        )
        by_day: dict[date, list[Asset]] = defaultdict(list)
        for asset in assets:
            by_day[asset.warranty_until].append(asset)
        # One entry per day; many devices bought together would flood the view.
        for day, items in sorted(by_day.items()):
            entries.append(
                Entry(
                    id=f"warranty-{day.isoformat()}",
                    kind="warranty",
                    title=str(len(items)),
                    start=day,
                    link={"name": "assets", "warranty_until": day.isoformat()},
                    details=[f"{a.inventory_number} · {a.model.full_name}" for a in items[:10]]
                    + ([f"+{len(items) - 10}"] if len(items) > 10 else []),
                )
            )

    if "license" in kinds:
        licenses = (
            License.objects.select_related("model__manufacturer")
            .filter(valid_until__gte=start, valid_until__lte=end)
            .annotate(used=Count("assignments"))
        )
        for lic in licenses:
            entries.append(
                Entry(
                    id=f"license-{lic.pk}",
                    kind="license",
                    title=lic.model.full_name,
                    start=lic.valid_until,
                    link={"name": "license", "id": str(lic.pk)},
                    details=[d for d in (lic.reference, f"{lic.used} / {lic.seats}") if d],
                )
            )

    return entries

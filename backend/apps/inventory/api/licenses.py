from datetime import date
from typing import Annotated
from uuid import UUID

from django.db.models import Count, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.accounts.permissions import ResourceKey
from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import AuthedRequest, permission_auth
from apps.core.exceptions import BusinessError
from apps.inventory.models import License
from apps.inventory.schemas.license import LicenseAssignIn, LicenseDetailOut, LicenseIn, LicenseOut
from apps.inventory.services import licenses as license_service
from apps.masterdata.models import Category

router = Router(tags=["licenses"], auth=permission_auth(ResourceKey.LICENSES))

SEARCH_FIELDS = (
    "model__name",
    "model__manufacturer__name",
    "reference",
    "license_key",
    "assignments__user__first_name",
    "assignments__user__last_name",
    "assignments__asset__inventory_number",
)
ORDERING_FIELDS = (
    "model__name",
    "model__category__sort_order",
    "model__category__name",
    "reference",
    "seats",
    "used_seats",
    "valid_until",
    # Groupings
    "assign_to",
    "supplier__name",
    "supplier_id",
    "created_at",
)


class LicenseFilter(FilterSchema):
    model: Annotated[list[UUID] | None, FilterLookup("model_id__in")] = None
    assign_to: Annotated[list[str] | None, FilterLookup("assign_to__in")] = None
    user: Annotated[list[UUID] | None, FilterLookup("assignments__user_id__in")] = None
    asset: Annotated[list[UUID] | None, FilterLookup("assignments__asset_id__in")] = None
    expires_from: Annotated[date | None, FilterLookup("valid_until__gte")] = None
    expires_until: Annotated[date | None, FilterLookup("valid_until__lte")] = None
    category: list[UUID] | None = None

    def filter_category(self, value: list[UUID] | None) -> Q:
        if not value:
            return Q()
        return Q(model__category_id__in=Category.descendant_ids_of(value))


def license_queryset() -> QuerySet[License]:
    return License.objects.select_related("model__manufacturer", "model__category", "supplier").annotate(
        used_seats=Count("assignments", distinct=True)
    )


@router.get("", response=list[LicenseOut])
@paginate(Pagination)
def list_licenses(
    request: AuthedRequest,
    filters: Query[LicenseFilter],
    q: str | None = None,
    ordering: str | None = None,
) -> QuerySet[License]:
    queryset = search(filters.filter(license_queryset()), q, SEARCH_FIELDS)
    return order(queryset, ordering, ORDERING_FIELDS)


@router.get("/{uuid:pk}", response=LicenseDetailOut)
def get_license(request: AuthedRequest, pk: UUID) -> License:
    return get_object_or_404(license_queryset(), pk=pk)


@router.post("", response={201: LicenseDetailOut})
def create_license(request: AuthedRequest, payload: LicenseIn) -> Status[License]:
    license = license_service.save_license(License(), payload.dict())
    return Status(201, get_license(request, license.pk))


@router.put("/{uuid:pk}", response=LicenseDetailOut)
def update_license(request: AuthedRequest, pk: UUID, payload: LicenseIn) -> License:
    license_service.save_license(get_object_or_404(License, pk=pk), payload.dict())
    return get_license(request, pk)


@router.delete("/{uuid:pk}", response={204: None})
def delete_license(request: AuthedRequest, pk: UUID) -> Status[None]:
    license = get_object_or_404(License, pk=pk)
    if license.assignments.exists():
        raise BusinessError(_("Remove all assignments before deleting the license."))
    license.delete()
    return Status(204, None)


@router.post("/{uuid:pk}/assignments", response={201: LicenseDetailOut})
def assign(request: AuthedRequest, pk: UUID, payload: LicenseAssignIn) -> Status[License]:
    license_service.assign_license(
        get_object_or_404(License, pk=pk),
        request.user,
        user_id=payload.user,
        asset_id=payload.asset,
        note=payload.note,
    )
    return Status(201, get_license(request, pk))


@router.delete("/{uuid:pk}/assignments/{uuid:assignment_id}", response=LicenseDetailOut)
def unassign(request: AuthedRequest, pk: UUID, assignment_id: UUID) -> License:
    assignment = get_object_or_404(get_object_or_404(License, pk=pk).assignments, pk=assignment_id)
    license_service.unassign_license(assignment, request.user)
    return get_license(request, pk)

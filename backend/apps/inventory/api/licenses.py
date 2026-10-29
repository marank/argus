from datetime import date
from typing import Annotated
from uuid import UUID

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import FilterLookup, FilterSchema, Query, Router, Status
from ninja.pagination import paginate

from apps.core.api.pagination import Pagination
from apps.core.api.querying import order, search
from apps.core.api.security import AuthedRequest, permission_auth
from apps.core.exceptions import BusinessError
from apps.inventory.models import License
from apps.inventory.schemas.license import LicenseAssignIn, LicenseDetailOut, LicenseIn, LicenseOut
from apps.inventory.services import licenses as license_service
from apps.masterdata.models import Category

router = Router(tags=["licenses"], auth=permission_auth("licenses"))

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
    "created_at",
)


class LicenseFilter(FilterSchema):
    model: Annotated[UUID | None, FilterLookup("model_id")] = None
    assign_to: str | None = None
    user: Annotated[UUID | None, FilterLookup("assignments__user_id")] = None
    asset: Annotated[UUID | None, FilterLookup("assignments__asset_id")] = None
    expires_before: Annotated[date | None, FilterLookup("valid_until__lt")] = None
    category: UUID | None = None

    def filter_category(self, value: UUID | None) -> Q:
        if not value:
            return Q()
        return Q(model__category_id__in=get_object_or_404(Category, pk=value).descendant_ids())


def license_queryset():
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
):
    queryset = search(filters.filter(license_queryset()), q, SEARCH_FIELDS)
    return order(queryset, ordering, ORDERING_FIELDS)


@router.get("/{uuid:pk}", response=LicenseDetailOut)
def get_license(request: AuthedRequest, pk: UUID):
    return get_object_or_404(license_queryset(), pk=pk)


@router.post("", response={201: LicenseDetailOut})
def create_license(request: AuthedRequest, payload: LicenseIn):
    license = license_service.save_license(License(), payload.dict())
    return Status(201, get_license(request, license.pk))


@router.put("/{uuid:pk}", response=LicenseDetailOut)
def update_license(request: AuthedRequest, pk: UUID, payload: LicenseIn):
    license_service.save_license(get_object_or_404(License, pk=pk), payload.dict())
    return get_license(request, pk)


@router.delete("/{uuid:pk}", response={204: None})
def delete_license(request: AuthedRequest, pk: UUID):
    license = get_object_or_404(License, pk=pk)
    if license.assignments.exists():
        raise BusinessError(_("Remove all assignments before deleting the license."))
    license.delete()
    return Status(204, None)


@router.post("/{uuid:pk}/assignments", response={201: LicenseDetailOut})
def assign(request: AuthedRequest, pk: UUID, payload: LicenseAssignIn):
    license_service.assign_license(
        get_object_or_404(License, pk=pk),
        request.user,
        user_id=payload.user,
        asset_id=payload.asset,
        note=payload.note,
    )
    return Status(201, get_license(request, pk))


@router.delete("/{uuid:pk}/assignments/{uuid:assignment_id}", response=LicenseDetailOut)
def unassign(request: AuthedRequest, pk: UUID, assignment_id: UUID):
    assignment = get_object_or_404(get_object_or_404(License, pk=pk).assignments, pk=assignment_id)
    license_service.unassign_license(assignment, request.user)
    return get_license(request, pk)

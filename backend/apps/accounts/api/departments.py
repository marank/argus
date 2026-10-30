from django.db.models import Case, Count, IntegerField, QuerySet, Value, When

from apps.accounts.models import Department
from apps.accounts.permissions import ResourceKey
from apps.accounts.schemas import DepartmentIn, DepartmentOut
from apps.core.api.crud import CrudConfig, build_crud_router


def department_queryset() -> QuerySet[Department]:
    # `tree_position`: parents before their subdepartments; the default order of every list.
    positions = Department.tree_positions()
    return (
        Department.objects.select_related("parent__parent__parent")
        .annotate(
            member_count=Count("members", distinct=True),
            tree_position=Case(
                *[When(pk=pk, then=Value(position)) for pk, position in positions.items()],
                default=Value(len(positions)),
                output_field=IntegerField(),
            ),
        )
        .prefetch_related("approvers")
        .order_by("tree_position")
    )


router = build_crud_router(
    CrudConfig(
        model=Department,
        out_schema=DepartmentOut,
        in_schema=DepartmentIn,
        permission=ResourceKey.DEPARTMENTS,
        search_fields=("name", "code", "cost_center"),
        ordering_fields=("name", "code", "cost_center", "sort_order", "tree_position"),
        queryset=department_queryset,
    ),
    tags=["departments"],
)

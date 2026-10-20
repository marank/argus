from django.db.models import Count

from apps.accounts.models import Department
from apps.accounts.schemas import DepartmentIn, DepartmentOut
from apps.core.api.crud import CrudConfig, build_crud_router

router = build_crud_router(
    CrudConfig(
        model=Department,
        out_schema=DepartmentOut,
        in_schema=DepartmentIn,
        search_fields=("name", "code", "cost_center"),
        ordering_fields=("name", "code", "cost_center", "sort_order"),
        queryset=lambda: Department.objects.annotate(
            member_count=Count("members", distinct=True)
        ).prefetch_related("approvers"),
    ),
    tags=["departments"],
)

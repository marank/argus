from django.http import HttpRequest

from apps.accounts.models import Role
from apps.accounts.permissions import RESOURCES
from apps.accounts.schemas.role import ResourceOut, RoleIn, RoleOut
from apps.core.api.crud import CrudConfig, build_crud_router
from apps.core.api.security import superuser_auth

# Roles decide who may change what, so only administrators see and edit them
# (the router is mounted with superuser auth in config/api.py).
router = build_crud_router(
    CrudConfig(
        model=Role,
        out_schema=RoleOut,
        in_schema=RoleIn,
        read_auth=superuser_auth,
        write_auth=superuser_auth,
        search_fields=("name", "description"),
        ordering_fields=("name",),
        queryset=lambda: Role.objects.prefetch_related("members"),
    ),
    tags=["roles"],
)


@router.get("/resources", response=list[ResourceOut])
def resources(request: HttpRequest):
    """The areas a role can grant, in the order of the role editor."""
    return RESOURCES

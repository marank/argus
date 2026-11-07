from typing import Any

from ninja import Router

from apps.accounts.permissions import ResourceKey
from apps.core.api.security import AuthedRequest, permission_auth
from apps.inventory.schemas.asset_import import AssetImportIn, AssetImportResultOut
from apps.inventory.services import asset_import

router = Router(tags=["assets"], auth=permission_auth(ResourceKey.ASSETS))


def _run(request: AuthedRequest, payload: AssetImportIn, *, dry_run: bool) -> asset_import.ImportResult:
    data: dict[str, Any] = payload.dict()
    rows = [{str(name): text for name, text in row.items()} for row in data["rows"]]
    return asset_import.import_assets(
        rows,
        request.user,
        defaults=data["defaults"],
        match_by=data["match_by"],
        existing=data["existing"],
        ignore_case=data["ignore_case"],
        dry_run=dry_run,
    )


@router.post("/preview", response=AssetImportResultOut)
def preview_import(request: AuthedRequest, payload: AssetImportIn) -> asset_import.ImportResult:
    """What importing the rows would do; nothing is saved."""
    return _run(request, payload, dry_run=True)


@router.post("", response=AssetImportResultOut)
def import_assets(request: AuthedRequest, payload: AssetImportIn) -> asset_import.ImportResult:
    """Create or update a device per row; rows with errors are left out."""
    return _run(request, payload, dry_run=False)

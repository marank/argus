from ninja import Router

from apps.accounts.permissions import ResourceKey
from apps.core.api.security import AuthedRequest, permission_auth
from apps.inventory.schemas.lookup import LookupOut
from apps.inventory.services.lookup import LookupResult, lookup_code

router = Router(tags=["lookup"], auth=permission_auth(ResourceKey.ASSETS))


@router.get("/lookup", response=LookupOut)
def lookup(request: AuthedRequest, code: str) -> LookupResult:
    """Resolve a scanned barcode to devices or a product model."""
    return lookup_code(code)

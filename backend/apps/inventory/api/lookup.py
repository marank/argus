from django.http import HttpRequest
from ninja import Router

from apps.core.api.security import permission_auth
from apps.inventory.schemas.lookup import LookupOut
from apps.inventory.services.lookup import lookup_code

router = Router(tags=["lookup"], auth=permission_auth("assets"))


@router.get("/lookup", response=LookupOut)
def lookup(request: HttpRequest, code: str):
    """Resolve a scanned barcode to devices or a product model."""
    return lookup_code(code)

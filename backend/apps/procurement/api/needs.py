from ninja import Router

from apps.core.api.security import AuthedRequest, permission_auth
from apps.procurement.schemas.needs import NeedsOut
from apps.procurement.services.needs import Needs, asset_request_needs, consumable_needs

router = Router(tags=["procurement"], auth=permission_auth("procurement"))


@router.get("", response=NeedsOut)
def list_needs(request: AuthedRequest) -> Needs:
    """Open demand from requests that the pool cannot cover, and consumables below their minimum."""
    return {"requests": asset_request_needs(), "consumables": consumable_needs()}

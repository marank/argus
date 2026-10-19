from django.http import HttpRequest
from ninja import Router

from apps.core.api.security import it_staff_auth
from apps.procurement.schemas.needs import NeedsOut
from apps.procurement.services.needs import consumable_needs, reservation_needs

router = Router(tags=["procurement"], auth=it_staff_auth)


@router.get("", response=NeedsOut)
def list_needs(request: HttpRequest):
    """Open demand from reservations that the pool cannot cover, and consumables below their minimum."""
    return {"reservations": reservation_needs(), "consumables": consumable_needs()}

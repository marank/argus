from ninja import Router

from . import allocations, portal, reservations, terminal

router = Router()
router.add_router("/reservations", reservations.router)
router.add_router("/reservations", allocations.router)
router.add_router("/portal", portal.router)
router.add_router("/terminal", terminal.router)

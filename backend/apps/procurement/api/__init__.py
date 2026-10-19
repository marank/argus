from ninja import Router

from . import needs, orders

router = Router()
router.add_router("/orders", orders.router)
router.add_router("/needs", needs.router)

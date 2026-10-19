from ninja import Router

from . import assets, events, lookup, stock

router = Router()
router.add_router("/assets", assets.router)
router.add_router("/stock", stock.router)
router.add_router("", events.router)
router.add_router("", lookup.router)

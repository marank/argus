from ninja import Router

from . import assets, consumables, events, licenses, lookup

router = Router()
router.add_router("/assets", assets.router)
router.add_router("/consumables", consumables.router)
router.add_router("/licenses", licenses.router)
router.add_router("", events.router)
router.add_router("", lookup.router)

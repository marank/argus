from ninja import Router

from . import asset_import, assets, consumables, events, issues, licenses, lookup

router = Router()
router.add_router("/assets/import", asset_import.router)
router.add_router("/assets", assets.router)
router.add_router("/consumables", consumables.router)
router.add_router("/licenses", licenses.router)
router.add_router("/issues", issues.router)
router.add_router("", events.router)
router.add_router("", lookup.router)

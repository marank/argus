from ninja import Router

from . import allocations, approvals, asset_requests, portal, terminal

router = Router()
router.add_router("/requests", asset_requests.router)
router.add_router("/requests", allocations.router)
router.add_router("/portal", portal.router)
router.add_router("/approvals", approvals.router)
router.add_router("/terminal", terminal.router)

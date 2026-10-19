"""Assembles the REST API from the routers of the individual apps."""

from django.core.exceptions import ValidationError
from django.db import connection
from django.http import Http404
from django.utils.translation import gettext as _
from ninja import NinjaAPI, Status

from apps.accounts.api import departments, users
from apps.core.api import number_sequences, session
from apps.core.api.security import employee_auth
from apps.core.exceptions import BusinessError
from apps.dashboard.api import calendar, overview
from apps.inventory.api import router as inventory_router
from apps.masterdata.api import asset_models, categories, locations, manufacturers, suppliers
from apps.procurement.api import router as procurement_router
from apps.reservations.api import router as reservations_router

api = NinjaAPI(title="Argus API", version="1.0.0", auth=employee_auth, urls_namespace="api")

api.add_router("/auth", session.router)
api.add_router("/dashboard", overview.router)
api.add_router("/calendar", calendar.router)
api.add_router("/accounts/users", users.router)
api.add_router("/accounts/departments", departments.router)
api.add_router("/masterdata/manufacturers", manufacturers.router)
api.add_router("/masterdata/suppliers", suppliers.router)
api.add_router("/masterdata/categories", categories.router)
api.add_router("/masterdata/locations", locations.router)
api.add_router("/masterdata/models", asset_models.router)
api.add_router("/masterdata/number-sequences", number_sequences.router)
api.add_router("/inventory", inventory_router)
api.add_router("", reservations_router)
api.add_router("/procurement", procurement_router)


@api.get("/health", auth=None, response={200: dict, 503: dict}, tags=["health"])
def health(request):
    """Liveness/readiness for container health checks: the app answers and the DB is reachable."""
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001 - any DB error means "not ready"
        return Status(503, {"status": "database unavailable"})
    return Status(200, {"status": "ok"})


@api.exception_handler(BusinessError)
def business_error(request, exc: BusinessError):
    return api.create_response(request, {"detail": exc.message}, status=409)


@api.exception_handler(ValidationError)
def validation_error(request, exc: ValidationError):
    if hasattr(exc, "error_dict"):
        errors = {field: [str(m) for m in messages] for field, messages in exc.message_dict.items()}
    else:
        errors = {"__all__": [str(m) for m in exc.messages]}
    detail = "; ".join(m for messages in errors.values() for m in messages)
    return api.create_response(request, {"detail": detail, "errors": errors}, status=422)


@api.exception_handler(Http404)
def not_found(request, exc):
    return api.create_response(request, {"detail": _("Not found.")}, status=404)

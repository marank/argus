from django.http import JsonResponse
from django.utils.translation import gettext as _

from apps.core.features import current_flags, guard_for


class ModuleGateMiddleware:
    """API calls of switched-off modules and features answer 404, as if they did not exist."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        key = guard_for(request.path_info)
        if key and not current_flags()[key]:
            return JsonResponse({"detail": _("This module is switched off.")}, status=404)
        return self.get_response(request)

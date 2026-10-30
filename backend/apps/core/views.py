from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponseRedirect


def admin_login(request: HttpRequest) -> HttpResponseRedirect:
    """Sends the Django admin's login to the app's (with the two-factor step), then back."""
    target = request.GET.get("next", "")
    if not target.startswith("/admin/"):
        target = "/admin/"
    return HttpResponseRedirect(f"/login?{urlencode({'next': target})}")

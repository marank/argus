from django.contrib import admin
from django.urls import path

from apps.core.views import admin_login
from config.api import api

urlpatterns = [
    # The admin signs in through the app, so the second sign-in step applies there too.
    path("admin/login/", admin_login),
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

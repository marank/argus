from django.contrib import admin
from django.urls import reverse


def test_every_admin_page_renders(admin_client):
    """Changelist, search and change form of every registered model load without errors."""
    for model, model_admin in admin.site._registry.items():
        opts = model._meta
        changelist = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
        response = admin_client.get(changelist, {"q": "a"} if model_admin.search_fields else {})
        assert response.status_code == 200, (changelist, response.status_code)

        if model_admin.has_add_permission(response.wsgi_request):
            add = reverse(f"admin:{opts.app_label}_{opts.model_name}_add")
            assert admin_client.get(add).status_code == 200, add

        obj = model._default_manager.first()
        if obj is not None:
            change = reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk])
            assert admin_client.get(change).status_code == 200, change

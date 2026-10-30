from django.contrib import admin

from apps.masterdata.models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin[Supplier]):
    list_display = ["name", "customer_number", "contact_person", "email", "phone", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "customer_number", "contact_person", "email"]

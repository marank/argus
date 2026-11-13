from django.contrib import admin

from apps.accounts.models import ApprovalDelegation


@admin.register(ApprovalDelegation)
class ApprovalDelegationAdmin(admin.ModelAdmin[ApprovalDelegation]):
    list_display = ["approver", "delegate", "starts_on", "ends_on"]
    search_fields = ["approver__username", "approver__last_name", "delegate__username", "delegate__last_name"]
    autocomplete_fields = ["approver", "delegate"]
    date_hierarchy = "starts_on"

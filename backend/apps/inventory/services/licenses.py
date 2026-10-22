from uuid import UUID

from django.db import transaction
from django.utils.translation import gettext as _

from apps.core.api.crud import apply_input
from apps.core.exceptions import BusinessError
from apps.inventory.models import Asset, License, LicenseAssignment

AssignTo = License.AssignTo


@transaction.atomic
def save_license(license: License, data: dict) -> License:
    """Create or update a license; seats and assignment type must fit the assignments."""
    if license.pk:
        used = license.assignments.count()
        if data.get("seats", license.seats) < used:
            raise BusinessError(
                _("%(used)s seats are assigned; remove assignments before reducing the seats.")
                % {"used": used}
            )
        if used and data.get("assign_to", license.assign_to) != license.assign_to:
            raise BusinessError(_("Remove all assignments before changing whom the license is assigned to."))
    return apply_input(license, data)


@transaction.atomic
def assign_license(
    license: License, user, *, user_id: UUID | None = None, asset_id: UUID | None = None, note: str = ""
) -> LicenseAssignment:
    license = License.objects.select_for_update().get(pk=license.pk)
    if license.assign_to == AssignTo.USER and not user_id:
        raise BusinessError(_("This license is assigned to employees. Choose an employee."))
    if license.assign_to == AssignTo.DEVICE and not asset_id:
        raise BusinessError(_("This license is assigned to devices. Choose a device."))
    if license.is_expired:
        raise BusinessError(_("The license has expired."))
    if license.assignments.count() >= license.seats:
        raise BusinessError(_("All %(seats)s seats of this license are in use.") % {"seats": license.seats})

    target = {"user_id": user_id} if license.assign_to == AssignTo.USER else {"asset_id": asset_id}
    if license.assignments.filter(**target).exists():
        raise BusinessError(_("Already assigned."))
    if asset_id and not Asset.objects.filter(pk=asset_id).exists():
        raise BusinessError(_("Device not found."))
    return LicenseAssignment.objects.create(license=license, assigned_by=user, note=note.strip(), **target)


@transaction.atomic
def unassign_license(assignment: LicenseAssignment, user) -> None:
    """Remove a seat; a seat handed out with a request counts as returned there."""
    from apps.requests.models import AssetRequestAllocation
    from apps.requests.services import workflow

    allocation = (
        AssetRequestAllocation.objects.filter(license_assignment=assignment)
        .select_related("item__asset_request")
        .first()
    )
    if allocation:
        workflow.release_from_elsewhere(allocation, user)
    LicenseAssignment.objects.filter(pk=assignment.pk).delete()

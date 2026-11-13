"""The user's own password (local accounts only)."""

import logging

from django.contrib.auth import update_session_auth_hash
from django.utils.translation import gettext as _
from ninja import Router, Status
from ninja.errors import HttpError

from apps.accounts.api.two_factor import confirm_password
from apps.accounts.schemas import PasswordChangeIn
from apps.accounts.services import passwords
from apps.core.api.security import AuthedRequest, employee_auth

logger = logging.getLogger(__name__)

router = Router(tags=["auth"], auth=employee_auth)


@router.post("", response={204: None})
def change_password(request: AuthedRequest, payload: PasswordChangeIn) -> Status[None]:
    """Needs the current password; this session stays signed in, others end."""
    user = request.user
    if user.is_ldap_user:
        raise HttpError(409, _("Change the password of a directory account in the directory."))
    if not passwords.may_change_own(user):
        raise HttpError(403, _("You may not change your password. Please contact IT."))
    confirm_password(request, payload.current_password)
    passwords.set_password(user, payload.new_password)
    update_session_auth_hash(request, user)
    logger.info("%s changed their password", user)
    return Status(204, None)

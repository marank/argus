"""Approvers delegate their approvals themselves, e.g. for a holiday."""

from typing import Any
from uuid import UUID

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja import Router, Status
from ninja.errors import HttpError

from apps.accounts.models import ApprovalDelegation, User
from apps.accounts.schemas import (
    ApprovalDelegationIn,
    ApprovalDelegationOut,
    ApprovalDelegationPeriodIn,
    DelegationsOut,
    UserRefOut,
)
from apps.accounts.services import delegations
from apps.core.api.querying import search_words
from apps.core.api.security import AuthedRequest, employee_auth

router = Router(tags=["approvals"], auth=employee_auth)


def require_approver(user: User) -> None:
    if not user.is_department_approver:
        raise HttpError(403, _("Only approvers of a department can delegate approvals."))


@router.get("", response=DelegationsOut)
def list_delegations(request: AuthedRequest) -> dict[str, Any]:
    today = timezone.localdate()
    not_ended = Q(ends_on__isnull=True) | Q(ends_on__gte=today)
    return {
        "departments": request.user.approving_departments.order_by("sort_order", "name"),
        "mine": delegations.current_and_future(request.user).select_related("approver"),
        "past": delegations.past(request.user),
        "received": ApprovalDelegation.objects.filter(not_ended, delegate=request.user)
        .select_related("approver", "delegate")
        .order_by("starts_on", "created_at"),
    }


@router.get("/candidates", response=list[UserRefOut])
def candidates(request: AuthedRequest, q: str = "") -> list[User]:
    """Active employees to choose a delegate from; needs at least two characters."""
    require_approver(request.user)
    words = search_words(q)
    if not words or len("".join(words)) < 2:
        return []
    people = User.objects.filter(is_active=True, is_terminal=False).exclude(pk=request.user.pk)
    for word in words:
        people = people.filter(
            Q(first_name__icontains=word) | Q(last_name__icontains=word) | Q(username__icontains=word)
        )
    return list(people.order_by("last_name", "first_name")[:15])


@router.post("", response={201: ApprovalDelegationOut})
def add_delegation(request: AuthedRequest, payload: ApprovalDelegationIn) -> Status[ApprovalDelegation]:
    require_approver(request.user)
    delegate = get_object_or_404(User, pk=payload.delegate)
    entry = delegations.add(request.user, delegate, payload.starts_on, payload.ends_on)
    return Status(201, entry)


def own_entry(request: AuthedRequest, pk: UUID) -> ApprovalDelegation:
    entries = ApprovalDelegation.objects.select_related("delegate", "approver")
    return get_object_or_404(entries, pk=pk, approver=request.user)


@router.put("/{uuid:pk}", response=ApprovalDelegationOut)
def change_period(
    request: AuthedRequest, pk: UUID, payload: ApprovalDelegationPeriodIn
) -> ApprovalDelegation:
    """A new period, e.g. back earlier or away longer."""
    return delegations.change_period(own_entry(request, pk), payload.starts_on, payload.ends_on)


@router.post("/{uuid:pk}/end", response={204: None})
def end_delegation(request: AuthedRequest, pk: UUID) -> Status[None]:
    """Back early: a running delegation ends now and stays in the history; a planned one goes."""
    delegations.end_now(own_entry(request, pk))
    return Status(204, None)


@router.delete("/{uuid:pk}", response={204: None})
def remove_delegation(request: AuthedRequest, pk: UUID) -> Status[None]:
    """Approvers remove their own delegations, planned, running or past."""
    own_entry(request, pk).delete()
    return Status(204, None)

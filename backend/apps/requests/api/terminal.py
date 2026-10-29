"""Shared pickup terminal: employees review prepared devices and sign for them."""

from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.accounts.models import User
from apps.core.api.querying import search, search_words
from apps.core.api.security import AuthedRequest, terminal_auth
from apps.requests.models import AssetRequest
from apps.requests.schemas.terminal import (
    TerminalPersonOut,
    TerminalPickupDetailOut,
    TerminalPickupOut,
    TerminalSignIn,
    TerminalStaffOut,
)
from apps.requests.services import workflow

from .queries import asset_request_queryset, get_for_update

router = Router(tags=["pickup terminal"], auth=terminal_auth)


def pickups(user):
    """Prepared pickups; a terminal with a site only lists pickups at that site."""
    queryset = asset_request_queryset().filter(
        status=AssetRequest.Status.READY, handover_mode=AssetRequest.HandoverMode.PICKUP
    )
    site = getattr(user, "terminal_location", None) if getattr(user, "is_terminal", False) else None
    if site is not None:
        queryset = queryset.filter(pickup_location_id__in=site.descendant_ids())
    return queryset


@router.get("/pickups", response=list[TerminalPickupOut])
def list_pickups(request: AuthedRequest, q: str | None = None):
    """Prepared pickups, next pickup first."""
    queryset = search(
        pickups(request.user),
        q,
        ("number", "requester__first_name", "requester__last_name", "requester__username"),
    )
    return list(queryset.order_by("pickup_at", "start_date"))


@router.get("/pickups/{uuid:pk}", response=TerminalPickupDetailOut)
def get_pickup(request: AuthedRequest, pk: UUID):
    return get_object_or_404(pickups(request.user), pk=pk)


@router.post("/pickups/{uuid:pk}/sign", response=TerminalPickupDetailOut)
@transaction.atomic
def sign(request: AuthedRequest, pk: UUID, payload: TerminalSignIn):
    """Complete the hand-out with the collecting person's signature."""
    asset_request = get_object_or_404(pickups(request.user), pk=pk)
    workflow.hand_out(
        get_for_update(asset_request.pk),
        request.user,
        method="signature",
        received_by_id=payload.received_by,
        received_by_name=payload.received_by_name,
        signature=payload.signature,
        notes=payload.notes,
        allocation_notes={n.allocation: n.note for n in payload.allocation_notes},
        handed_out_by_id=payload.handed_out_by,
    )
    return get_object_or_404(asset_request_queryset(), pk=pk)


@router.get("/staff", response=list[TerminalStaffOut])
def staff(request: AuthedRequest):
    """IT staff members, to name who hands out when it is not the one who prepared the pickup."""
    return list(User.objects.filter(is_active=True, is_staff=True, is_terminal=False))


@router.get("/people", response=list[TerminalPersonOut])
def people(request: AuthedRequest, q: str = ""):
    """Minimal employee lookup to record who collects the devices.

    Every word must match the first or last name, the username or the employee
    number, so "anna sch" finds Anna Schmidt.
    """
    if len(q.strip()) < 2:
        return []
    people = User.objects.filter(is_active=True, is_terminal=False)
    for word in search_words(q):
        people = people.filter(
            Q(first_name__icontains=word)
            | Q(last_name__icontains=word)
            | Q(username__icontains=word)
            | Q(employee_number__iexact=word)
        )
    return list(people.select_related("department")[:15])

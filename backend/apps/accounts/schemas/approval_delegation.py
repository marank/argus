from datetime import date
from typing import Literal
from uuid import UUID

from apps.accounts.models import ApprovalDelegation
from apps.accounts.schemas.user import UserRefOut
from apps.core.schemas import RefOut
from apps.core.schemas.base import Schema

DelegationStatus = Literal["running", "planned", "ended"]


class ApprovalDelegationOut(Schema):
    id: UUID
    approver: UserRefOut
    delegate: UserRefOut
    starts_on: date
    # None: until removed.
    ends_on: date | None
    status: DelegationStatus

    @staticmethod
    def resolve_status(obj: ApprovalDelegation) -> str:
        from apps.accounts.services import delegations

        return delegations.status(obj)


class ApprovalDelegationIn(Schema):
    delegate: UUID
    starts_on: date
    ends_on: date | None = None


class ApprovalDelegationPeriodIn(Schema):
    starts_on: date
    ends_on: date | None = None


class DelegationsOut(Schema):
    # Departments the user approves for as named approver (empty for delegations only).
    departments: list[RefOut]
    # Delegations the user named as approver, current and upcoming.
    mine: list[ApprovalDelegationOut]
    # The user's last delegations whose period is over.
    past: list[ApprovalDelegationOut]
    # Approvers the user stands in for, current and upcoming.
    received: list[ApprovalDelegationOut]

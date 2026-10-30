from typing import Any
from uuid import UUID

from ninja import Schema

from apps.accounts.models import Department, User
from apps.core.schemas import RefOut, per_response

from .user import UserRefOut


class DepartmentOut(Schema):
    id: UUID
    name: str
    icon: Department.Icon
    code: str
    cost_center: str
    sort_order: int
    member_count: int = 0
    parent: RefOut | None = None
    path: list[str] = []
    approvers: list[UserRefOut] = []
    # The approvers that decide: the own or, without any, those of the nearest department above.
    effective_approvers: list[UserRefOut] = []

    @staticmethod
    def resolve_member_count(obj: Department) -> int:
        # Annotated by the list endpoint; counted only where it is missing (e.g. after saving).
        count = getattr(obj, "member_count", None)
        return obj.members.count() if count is None else count

    @staticmethod
    def resolve_path(obj: Department) -> list[str]:
        return [d.name for d in reversed(obj.ancestors())] + [obj.name]

    @staticmethod
    def resolve_approvers(obj: Department) -> list[User]:
        return list(obj.approvers.all())

    @staticmethod
    def resolve_effective_approvers(obj: Department, context: dict[str, Any] | None) -> list[User]:
        source = per_response(context, "department_approval_sources", Department.approval_sources).get(obj.pk)
        if source is None:
            return []
        return list(User.objects.filter(approving_departments=source, is_active=True))


class DepartmentIn(Schema):
    name: str
    icon: Department.Icon = Department.Icon.BUILDING
    code: str = ""
    cost_center: str = ""
    parent: UUID | None = None
    sort_order: int = 0
    approvers: list[UUID] = []

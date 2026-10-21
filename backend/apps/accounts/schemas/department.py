from uuid import UUID

from ninja import ModelSchema, Schema

from apps.accounts.models import Department

from .user import UserRefOut


class DepartmentOut(ModelSchema):
    member_count: int = 0
    approvers: list[UserRefOut] = []

    class Meta:
        model = Department
        fields = ["id", "name", "code", "cost_center", "sort_order"]

    @staticmethod
    def resolve_member_count(obj: Department) -> int:
        # Annotated by the list endpoint; counted only where it is missing (e.g. after saving).
        count = getattr(obj, "member_count", None)
        return obj.members.count() if count is None else count

    @staticmethod
    def resolve_approvers(obj: Department) -> list:
        return list(obj.approvers.all())


class DepartmentIn(Schema):
    name: str
    code: str = ""
    cost_center: str = ""
    sort_order: int = 0
    approvers: list[UUID] = []

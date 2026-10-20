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
        return getattr(obj, "member_count", None) or obj.members.count()

    @staticmethod
    def resolve_approvers(obj: Department) -> list:
        return list(obj.approvers.all())


class DepartmentIn(Schema):
    name: str
    code: str = ""
    cost_center: str = ""
    sort_order: int = 0
    approvers: list[UUID] = []

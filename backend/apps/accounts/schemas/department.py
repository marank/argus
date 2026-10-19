from ninja import ModelSchema, Schema

from apps.accounts.models import Department


class DepartmentOut(ModelSchema):
    member_count: int = 0

    class Meta:
        model = Department
        fields = ["id", "name", "code", "cost_center"]

    @staticmethod
    def resolve_member_count(obj: Department) -> int:
        return getattr(obj, "member_count", None) or obj.members.count()


class DepartmentIn(Schema):
    name: str
    code: str = ""
    cost_center: str = ""

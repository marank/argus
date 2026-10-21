from ninja import Field, ModelSchema, Schema

from apps.core.models import NumberSequence


class NumberSequenceOut(ModelSchema):
    preview: str

    class Meta:
        model = NumberSequence
        fields = [
            "id",
            "code",
            "name",
            "prefix",
            "pattern",
            "padding",
            "next_value",
            "reset_period",
            "is_system",
        ]

    @staticmethod
    def resolve_preview(obj: NumberSequence) -> str:
        return obj.preview()


class NumberSequenceIn(Schema):
    name: str
    code: str = ""
    prefix: str = ""
    pattern: str = "{prefix}{seq}"
    padding: int = Field(5, ge=1, le=12)
    next_value: int = Field(1, ge=1)
    reset_period: NumberSequence.ResetPeriod = NumberSequence.ResetPeriod.NEVER

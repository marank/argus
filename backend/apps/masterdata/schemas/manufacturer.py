from ninja import ModelSchema, Schema

from apps.masterdata.models import Manufacturer


class ManufacturerOut(ModelSchema):
    class Meta:
        model = Manufacturer
        fields = ["id", "name", "website", "support_url", "support_phone", "notes", "is_active"]


class ManufacturerIn(Schema):
    name: str
    website: str = ""
    support_url: str = ""
    support_phone: str = ""
    notes: str = ""
    is_active: bool = True

from ninja import ModelSchema, Schema

from apps.masterdata.models import Supplier


class SupplierOut(ModelSchema):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "customer_number",
            "contact_person",
            "email",
            "phone",
            "website",
            "address",
            "notes",
            "is_active",
        ]


class SupplierIn(Schema):
    name: str
    customer_number: str = ""
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    address: str = ""
    notes: str = ""
    is_active: bool = True

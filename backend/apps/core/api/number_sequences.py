from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Schema

from apps.core.api.crud import CrudConfig, build_crud_router
from apps.core.api.security import it_staff_auth
from apps.core.models import NumberSequence
from apps.core.schemas.number_sequence import NumberSequenceIn, NumberSequenceOut

router = build_crud_router(
    CrudConfig(
        model=NumberSequence,
        out_schema=NumberSequenceOut,
        in_schema=NumberSequenceIn,
        permission="number_sequences",
        search_fields=("code", "name", "prefix"),
        ordering_fields=("name", "code"),
    ),
    tags=["number sequences"],
)


class PreviewOut(Schema):
    examples: list[str]


@router.post("/preview", response=PreviewOut, auth=it_staff_auth)
def preview(request: HttpRequest, payload: NumberSequenceIn):
    """Render a few example numbers for an unsaved configuration."""
    sequence = NumberSequence(**payload.dict())
    sequence.clean()
    start = payload.next_value
    return {"examples": [sequence.format(v) for v in range(start, start + 3)]}


@router.get("/{uuid:pk}/peek", response=PreviewOut)
def peek(request: HttpRequest, pk: UUID):
    sequence = get_object_or_404(NumberSequence, pk=pk)
    return {"examples": [sequence.preview()]}

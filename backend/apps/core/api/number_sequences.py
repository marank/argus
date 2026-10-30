from uuid import UUID

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja import Schema
from ninja.errors import HttpError

from apps.accounts.permissions import WRITE
from apps.core.api.crud import CrudConfig, build_crud_router
from apps.core.api.security import AuthedRequest, permission_auth
from apps.core.models import NumberSequence
from apps.core.schemas.number_sequence import NumberSequenceIn, NumberSequenceOut


def keep_system_sequences(request: AuthedRequest, sequence: NumberSequence) -> None:
    if sequence.is_system:
        raise HttpError(409, _("Argus draws numbers from this sequence; it cannot be deleted."))


router = build_crud_router(
    CrudConfig(
        model=NumberSequence,
        out_schema=NumberSequenceOut,
        in_schema=NumberSequenceIn,
        permission="number_sequences",
        check_delete=keep_system_sequences,
        search_fields=("code", "name", "prefix"),
        ordering_fields=("name", "code"),
    ),
    tags=["number sequences"],
)


class PreviewOut(Schema):
    examples: list[str]


@router.post("/preview", response=PreviewOut, auth=permission_auth("number_sequences", WRITE))
def preview(request: AuthedRequest, payload: NumberSequenceIn) -> dict[str, list[str]]:
    """Render a few example numbers for an unsaved configuration."""
    sequence = NumberSequence(**payload.dict())
    sequence.clean()
    start = payload.next_value
    return {"examples": [sequence.format(v) for v in range(start, start + 3)]}


@router.get("/{uuid:pk}/peek", response=PreviewOut)
def peek(request: AuthedRequest, pk: UUID) -> dict[str, list[str]]:
    sequence = get_object_or_404(NumberSequence, pk=pk)
    return {"examples": [sequence.preview()]}

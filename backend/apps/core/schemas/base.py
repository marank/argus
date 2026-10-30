"""Base class of every API schema in Argus."""

from typing import ClassVar

from ninja import Schema as NinjaSchema
from pydantic import ConfigDict


class Schema(NinjaSchema):
    """``ninja.Schema`` whose responses list every field as present.

    A response always contains each field, also one that has a default, but pydantic
    would publish such fields as optional, and the frontend's generated types would
    then have to handle values that never go missing. Input validation is unaffected.
    Use this class for all schemas (a test checks it).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(json_schema_serialization_defaults_required=True)

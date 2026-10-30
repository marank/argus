import typing

from apps.requests.models import AssetRequestEventKind
from apps.requests.schemas.asset_request import AssetRequestEventOut


def test_every_event_kind_has_exactly_one_schema():
    union, _ = typing.get_args(AssetRequestEventOut.__value__)
    kinds = [
        kind
        for schema in typing.get_args(union)
        for kind in typing.get_args(schema.model_fields["kind"].annotation)
    ]
    assert sorted(kinds) == sorted(AssetRequestEventKind)

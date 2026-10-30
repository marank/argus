from typing import Literal

from ninja import Schema

from apps.masterdata.schemas.asset_model import AssetModelOut

from .asset import AssetOut


class LookupOut(Schema):
    kind: Literal["asset", "model", "multiple", "none"]
    assets: list[AssetOut]
    models: list[AssetModelOut]

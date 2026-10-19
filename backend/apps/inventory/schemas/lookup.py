from ninja import Schema

from apps.masterdata.schemas.asset_model import AssetModelOut

from .asset import AssetOut


class LookupOut(Schema):
    kind: str
    assets: list[AssetOut]
    models: list[AssetModelOut]

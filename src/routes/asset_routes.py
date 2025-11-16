# src/routes/asset_routes.py
from __future__ import annotations

from typing import Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config.assets import ASSETS, AssetConfig
from src.services.market_data_service import get_historical_series
from src.services.indicator_service import compute_indicators
from src.services.confidence_engine import AssetIndicators, AssetConfidence, _compute_asset_score

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetInfo(BaseModel):
    id: str
    name: str
    category: str
    data_source: str


class AssetListResponse(BaseModel):
    assets: Dict[str, AssetInfo]


class AssetDetailResponse(BaseModel):
    config: AssetInfo
    latest_price: float
    indicators: AssetIndicators | None
    confidence_score: float | None


@router.get("/", response_model=AssetListResponse)
async def list_assets():
    assets = {
        aid: AssetInfo(
            id=cfg.id,
            name=cfg.name,
            category=cfg.category.value,
            data_source=cfg.data_source.value,
        )
        for aid, cfg in ASSETS.items()
    }
    return AssetListResponse(assets=assets)


@router.get("/{asset_id}", response_model=AssetDetailResponse)
async def get_asset_details(asset_id: str, lookback_days: int = 30):
    cfg: AssetConfig | None = ASSETS.get(asset_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail="Unknown asset_id")

    series = await get_historical_series(asset_id, lookback_days=lookback_days)
    latest_price = series[-1].price if series else 0.0
    inds = compute_indicators(series)

    if inds is None:
        indicators_model = None
        confidence_score = None
    else:
        confidence_score = _compute_asset_score(inds)
        indicators_model = AssetIndicators(
            momentum=inds.momentum,
            trend=inds.trend,
            volatility=inds.volatility,
        )

    return AssetDetailResponse(
        config=AssetInfo(
            id=cfg.id,
            name=cfg.name,
            category=cfg.category.value,
            data_source=cfg.data_source.value,
        ),
        latest_price=latest_price,
        indicators=indicators_model,
        confidence_score=confidence_score,
    )

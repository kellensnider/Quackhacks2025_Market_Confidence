# src/routes/polymarket_routes.py
from __future__ import annotations

from typing import Dict
from fastapi import APIRouter
from pydantic import BaseModel

from src.services.polymarket_service import (
    get_all_polymarket_sentiment,
    PolymarketMarketSentiment,
)
from src.services.confidence_engine import PolymarketSentiment
from src.services.confidence_engine import build_confidence_breakdown

router = APIRouter(prefix="/polymarket", tags=["polymarket"])


class PolymarketListResponse(BaseModel):
    markets: Dict[str, PolymarketMarketSentiment]


@router.get("/markets", response_model=PolymarketListResponse)
async def list_polymarket_markets():
    """
    Return raw Polymarket sentiment for each tracked market.
    """
    markets = await get_all_polymarket_sentiment()
    return PolymarketListResponse(markets=markets)


@router.get("/sentiment", response_model=PolymarketSentiment)
async def get_polymarket_sentiment(lookback_days: int = 30):
    """
    Return Polymarket sentiment as used in the confidence engine.
    (This reuses the same computation as /confidence to stay consistent.)
    """
    breakdown = await build_confidence_breakdown(lookback_days=lookback_days)
    return breakdown.polymarket_sentiment

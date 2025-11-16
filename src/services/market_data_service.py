# src/services/market_data_service.py
from __future__ import annotations

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import time

import yfinance as yf

from src.config.assets import ASSETS, DataSource, AssetConfig
from src.services.cache import cache
from src.utils.http import get_json


class MarketDataPoint(BaseModel):
    timestamp: int  # unix seconds
    price: float


COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


async def _fetch_coingecko_price(asset: AssetConfig) -> Optional[float]:
    if not asset.coingecko_id:
        return None
    url = f"{COINGECKO_BASE_URL}/simple/price"
    params = {"ids": asset.coingecko_id, "vs_currencies": "usd"}
    data = await get_json(url, params=params)
    try:
        return float(data[asset.coingecko_id]["usd"])
    except Exception:
        return None


async def _fetch_coingecko_history(asset: AssetConfig, lookback_days: int) -> List[MarketDataPoint]:
    if not asset.coingecko_id:
        return []
    url = f"{COINGECKO_BASE_URL}/coins/{asset.coingecko_id}/market_chart"
    params = {"vs_currency": "usd", "days": lookback_days}
    data = await get_json(url, params=params)

    prices = data.get("prices", [])
    points: List[MarketDataPoint] = []
    for ts_ms, price in prices:
        points.append(
            MarketDataPoint(
                timestamp=int(ts_ms / 1000),  # convert ms -> seconds
                price=float(price),
            )
        )
    return points


async def _fetch_yfinance_history(asset: AssetConfig, lookback_days: int) -> List[MarketDataPoint]:
    if not asset.yfinance_symbol:
        return []

    # yfinance is synchronous, so we just call it in this async func.
    end = datetime.utcnow()
    start = end - timedelta(days=lookback_days)
    ticker = yf.Ticker(asset.yfinance_symbol)
    hist = ticker.history(start=start, end=end, interval="1d")

    points: List[MarketDataPoint] = []
    # hist index is pandas datetime; we just iterate rows
    for ts, row in hist.iterrows():
        price = float(row["Close"])
        points.append(
            MarketDataPoint(
                timestamp=int(ts.timestamp()),
                price=price,
            )
        )
    return points


async def get_latest_price(asset_id: str) -> Optional[float]:
    """
    Get latest price for the given asset (from cache if possible).
    """
    cache_key = f"latest_price:{asset_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    asset = ASSETS[asset_id]
    price: Optional[float] = None

    if asset.data_source == DataSource.COINGECKO:
        price = await _fetch_coingecko_price(asset)
    elif asset.data_source == DataSource.YFINANCE:
        # Quick hack: just get the last close via history
        series = await _fetch_yfinance_history(asset, lookback_days=2)
        if series:
            price = series[-1].price

    if price is not None:
        cache.set(cache_key, price, ttl_seconds=60)  # 1 minute cache

    return price


async def get_historical_series(asset_id: str, lookback_days: int = 30) -> List[MarketDataPoint]:
    """
    Fetch historical daily price series for an asset.

    Returns:
        List of MarketDataPoint sorted by timestamp ascending.
    """
    cache_key = f"history:{asset_id}:{lookback_days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    asset = ASSETS[asset_id]

    if asset.data_source == DataSource.COINGECKO:
        series = await _fetch_coingecko_history(asset, lookback_days)
    elif asset.data_source == DataSource.YFINANCE:
        series = await _fetch_yfinance_history(asset, lookback_days)
    else:
        series = []

    # sort by timestamp just in case
    series = sorted(series, key=lambda p: p.timestamp)
    cache.set(cache_key, series, ttl_seconds=60)  # 1 minute cache

    return series

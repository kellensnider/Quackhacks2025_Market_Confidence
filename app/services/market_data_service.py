from typing import List
from pydantic import BaseModel
import time
import random
import httpx

from app.config.assets import ASSETS, AssetConfig


class PricePoint(BaseModel):
    timestamp: int  # ms since epoch
    close: float


class AssetTimeSeries(BaseModel):
    assetId: str
    data: List[PricePoint]


async def _fetch_from_coingecko(asset: AssetConfig) -> AssetTimeSeries:
    """
    For BTC (or other CoinGecko coins). 30 days of daily prices.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.coingecko.com/api/v3/coins/{asset.symbol}/market_chart",
            params={"vs_currency": "usd", "days": 30, "interval": "daily"},
            timeout=10,
        )
        resp.raise_for_status()
        raw = resp.json()

    prices = raw.get("prices", [])
    points = [
        PricePoint(timestamp=int(ts), close=float(price))
        for ts, price in prices
    ]

    return AssetTimeSeries(assetId=asset.id, data=points)


async def _fetch_stub_series(asset: AssetConfig) -> AssetTimeSeries:
    """
    Dummy data generator for non-crypto assets – enough for hackathon visuals.
    """
    now = int(time.time() * 1000)
    points: List[PricePoint] = []

    base = 100.0
    for i in range(30, -1, -1):
        # Slight random walk
        base += random.uniform(-1.0, 1.5)
        points.append(
            PricePoint(
                timestamp=now - i * 24 * 60 * 60 * 1000,
                close=round(base, 2),
            )
        )

    return AssetTimeSeries(assetId=asset.id, data=points)


async def get_all_asset_series() -> List[AssetTimeSeries]:
    series: List[AssetTimeSeries] = []

    for asset in ASSETS:
        if asset.source == "coingecko":
            ts = await _fetch_from_coingecko(asset)
        else:
            ts = await _fetch_stub_series(asset)
        series.append(ts)

    return series

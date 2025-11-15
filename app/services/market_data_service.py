from typing import List
from pydantic import BaseModel
import time
import random

import httpx
import yfinance as yf

from app.config.assets import ASSETS, AssetConfig


class PricePoint(BaseModel):
    timestamp: int  # ms since epoch
    close: float


class AssetTimeSeries(BaseModel):
    assetId: str
    data: List[PricePoint]


# ------------- CoinGecko (for BTC) -------------

async def _fetch_from_coingecko(asset: AssetConfig) -> AssetTimeSeries:
    """
    For BTC (or other CoinGecko coins). Last 30 days of daily prices.
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


# ------------- yfinance (for SPY, QQQ, XLK, GLD, etc.) -------------

async def _fetch_from_yfinance(asset: AssetConfig) -> AssetTimeSeries:
    """
    Fetch ~30 recent daily closes for an equity/ETF via yfinance.

    Uses asset.symbol as the ticker (e.g. SPY, QQQ, XLK, GLD).
    """
    if not asset.symbol:
        # fallback if symbol is missing
        return await _fetch_stub_series(asset)

    # yfinance is sync, but it's fine to call directly in a simple async app
    ticker = yf.Ticker(asset.symbol)
    # 1mo of daily data is plenty for our indicators
    hist = ticker.history(period="1mo", interval="1d")

    if hist.empty:
        # fallback if no data
        return await _fetch_stub_series(asset)

    points: List[PricePoint] = []
    # hist.index is a DatetimeIndex; hist["Close"] is a Series
    for ts, row in hist.iterrows():
        # ts is a pandas Timestamp, convert to ms since epoch
        ts_ms = int(ts.timestamp() * 1000)
        close = float(row["Close"])
        points.append(PricePoint(timestamp=ts_ms, close=close))

    # keep only last 30 points, sorted ascending
    points = sorted(points, key=lambda p: p.timestamp)[-30:]

    return AssetTimeSeries(assetId=asset.id, data=points)


# ------------- Stub (for macros / fallback) -------------

async def _fetch_stub_series(asset: AssetConfig) -> AssetTimeSeries:
    """
    Dummy data generator – used as fallback or for macro assets
    we haven't wired to real APIs yet (housing, CPI, 10Y, etc.).
    """
    now = int(time.time() * 1000)
    points: List[PricePoint] = []

    base = 100.0
    for i in range(30, -1, -1):
        base += random.uniform(-1.0, 1.5)
        points.append(
            PricePoint(
                timestamp=now - i * 24 * 60 * 60 * 1000,
                close=round(base, 2),
            )
        )

    return AssetTimeSeries(assetId=asset.id, data=points)


# ------------- Dispatcher -------------

async def get_all_asset_series() -> List[AssetTimeSeries]:
    """
    Dispatch to the right provider based on asset.source.
    BTC uses CoinGecko, equities/GLD use yfinance, macros use stub for now.
    """
    series: List[AssetTimeSeries] = []

    for asset in ASSETS:
        if asset.source == "coingecko":
            ts = await _fetch_from_coingecko(asset)
        elif asset.source == "yfinance":
            ts = await _fetch_from_yfinance(asset)
        else:
            ts = await _fetch_stub_series(asset)

        series.append(ts)

    return series

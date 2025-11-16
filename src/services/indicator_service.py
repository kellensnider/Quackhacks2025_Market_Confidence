# src/services/indicator_service.py
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
import math

from src.services.market_data_service import MarketDataPoint
from src.utils.normalize import (
    normalize_momentum,
    normalize_trend,
    normalize_volatility,
)


class Indicators(BaseModel):
    momentum: float   # normalized 0–1
    trend: float      # normalized 0–1
    volatility: float # normalized 0–1 (higher usually = better if invert=True in normalize_volatility)


def _percent_change(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return (new - old) / old


def _moving_average(prices: List[float]) -> float:
    if not prices:
        return 0.0
    return sum(prices) / len(prices)


def _stdev(prices: List[float]) -> float:
    if len(prices) < 2:
        return 0.0
    mean = _moving_average(prices)
    var = sum((p - mean) ** 2 for p in prices) / (len(prices) - 1)
    return math.sqrt(var)


def compute_indicators(series: List[MarketDataPoint]) -> Optional[Indicators]:
    """
    Compute normalized indicators for a single asset.

    - Momentum: % change over full lookback window.
    - Trend: price vs. simple moving average.
    - Volatility: stddev of daily returns, normalized (lower vol => higher score).

    Returns:
        Indicators or None if insufficient data.
    """
    if len(series) < 2:
        return None

    prices = [p.price for p in series]
    first_price = prices[0]
    last_price = prices[-1]

    # Momentum: full-window percent change
    raw_return = _percent_change(first_price, last_price)
    norm_momentum = normalize_momentum(raw_return)

    # Trend: last price vs. moving average
    ma = _moving_average(prices)
    if ma == 0:
        price_vs_ma = 1.0
    else:
        price_vs_ma = last_price / ma
    norm_trend = normalize_trend(price_vs_ma)

    # Volatility: stdev of daily returns
    daily_returns = []
    for i in range(1, len(prices)):
        daily_returns.append(_percent_change(prices[i - 1], prices[i]))
    stdev_returns = _stdev(daily_returns)
    norm_vol = normalize_volatility(stdev_returns, invert=True)

    return Indicators(
        momentum=norm_momentum,
        trend=norm_trend,
        volatility=norm_vol,
    )

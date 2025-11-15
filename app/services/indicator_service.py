from typing import List
from pydantic import BaseModel

from app.services.market_data_service import AssetTimeSeries
from app.utils.normalize import normalize_to_score


class AssetIndicators(BaseModel):
    assetId: str
    momentum1d: float
    momentum7d: float
    momentum30d: float
    above50dma: bool
    above200dma: bool
    volScore: float
    momentumScore: float


def _pct_change(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return (a - b) / b * 100.0


def _simple_moving_average(values: List[float], window: int) -> float:
    if not values:
        return 0.0
    if len(values) < window:
        return sum(values) / len(values)
    subset = values[-window:]
    return sum(subset) / len(subset)


def _sample_std_dev(values: List[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return variance ** 0.5


def compute_asset_indicators(series: AssetTimeSeries) -> AssetIndicators:
    closes = [p.close for p in series.data]
    if not closes:
        # Entirely empty — return neutral
        return AssetIndicators(
            assetId=series.assetId,
            momentum1d=0.0,
            momentum7d=0.0,
            momentum30d=0.0,
            above50dma=False,
            above200dma=False,
            volScore=50.0,
            momentumScore=50.0,
        )

    latest = closes[-1]
    d1 = closes[-2] if len(closes) >= 2 else latest
    d7 = closes[-8] if len(closes) >= 8 else closes[0]
    d30 = closes[0]

    momentum1d = _pct_change(latest, d1)
    momentum7d = _pct_change(latest, d7)
    momentum30d = _pct_change(latest, d30)

    sma50 = _simple_moving_average(closes, 50)
    sma200 = _simple_moving_average(closes, 200)

    daily_returns = [
        _pct_change(closes[i], closes[i - 1])
        for i in range(1, len(closes))
    ]
    vol = _sample_std_dev(daily_returns)

    vol_score = normalize_to_score(vol, 0, 5)               # 0–5% stddev
    m_score_short = normalize_to_score(momentum7d, -10, 10)
    m_score_long = normalize_to_score(momentum30d, -20, 20)
    momentum_score = 0.4 * m_score_short + 0.6 * m_score_long

    return AssetIndicators(
        assetId=series.assetId,
        momentum1d=momentum1d,
        momentum7d=momentum7d,
        momentum30d=momentum30d,
        above50dma=latest > sma50,
        above200dma=latest > sma200,
        volScore=vol_score,
        momentumScore=momentum_score,
    )


def compute_all_indicators(all_series: List[AssetTimeSeries]) -> List[AssetIndicators]:
    return [compute_asset_indicators(ts) for ts in all_series]

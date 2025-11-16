# src/utils/normalize.py
from __future__ import annotations

from typing import Tuple


def _clip(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def normalize_momentum(
    return_pct: float,
    min_return: float = -0.20,
    max_return: float = 0.20,
) -> float:
    """
    Normalize a % return into [0, 1].

    Args:
        return_pct: e.g. 0.05 for +5% over lookback.
        min_return: worst-case bound (e.g. -20%).
        max_return: best-case bound (e.g. +20%).

    Returns:
        float in [0, 1], where 0 is very negative momentum,
        0.5 is neutral, and 1 is very strong positive momentum.
    """
    clipped = _clip(return_pct, min_return, max_return)
    # Map [min_return, max_return] -> [0,1]
    return (clipped - min_return) / (max_return - min_return)


def normalize_trend(price_vs_ma_ratio: float, min_ratio: float = 0.9, max_ratio: float = 1.1) -> float:
    """
    Normalize trend as price / moving_average into [0,1].

    Args:
        price_vs_ma_ratio: e.g. 1.05 means price 5% above MA.
        min_ratio: lower bound for ratio (e.g. 0.9 = 10% below MA).
        max_ratio: upper bound for ratio (e.g. 1.1 = 10% above MA).

    Returns:
        float in [0, 1]. 0.5 is roughly 'at MA'.
        >0.5 means price above MA (uptrend).
        <0.5 means price below MA (downtrend).
    """
    clipped = _clip(price_vs_ma_ratio, min_ratio, max_ratio)
    return (clipped - min_ratio) / (max_ratio - min_ratio)


def normalize_volatility(
    stdev_pct: float,
    low_vol: float = 0.05,
    high_vol: float = 0.40,
    invert: bool = True,
) -> float:
    """
    Normalize volatility into [0,1].

    Args:
        stdev_pct: standard deviation of returns, e.g. 0.15 for 15%.
        low_vol: volatility level considered 'very calm'.
        high_vol: volatility level considered 'very turbulent'.
        invert: if True, low volatility => higher normalized score.

    Returns:
        float in [0,1]. If invert=True, then:
            - low volatility => near 1
            - high volatility => near 0
    """
    clipped = _clip(stdev_pct, low_vol, high_vol)
    raw = (clipped - low_vol) / (high_vol - low_vol)  # 0 (calm) -> 1 (turbulent)
    if invert:
        return 1.0 - raw
    return raw


def normalize_polymarket_probability(probability: float) -> float:
    """
    Ensure a Polymarket probability stays in [0,1] and return it.

    Args:
        probability: raw prob (0–1 or 0–100 if mis-scaled).

    Returns:
        float in [0,1].
    """
    # Handle potential 0–100 input (just in case)
    if probability > 1.0:
        probability = probability / 100.0
    return _clip(probability, 0.0, 1.0)


def to_percentage(score_0_1: float) -> float:
    """
    Convert a [0,1] score to [0,100].

    Args:
        score_0_1: float between 0 and 1.

    Returns:
        float between 0 and 100.
    """
    return _clip(score_0_1, 0.0, 1.0) * 100.0

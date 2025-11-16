# src/services/confidence_engine.py
from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel

#from src.config.assets import ASSETS, CATEGORY_TO_ASSETS, AssetCategory
from src.config.assets import (
    ASSETS,
    CATEGORY_TO_ASSETS,
    AssetCategory,
    AssetDirection,   # 👈 NEW
)

from src.config.weights import (
    ASSET_WEIGHTS,
    CATEGORY_WEIGHTS,
    POLYMARKET_WEIGHTS,
  # 
)

from src.services.market_data_service import get_historical_series, MarketDataPoint
from src.services.indicator_service import compute_indicators, Indicators
from src.services.polymarket_service import (
    get_polymarket_sentiment,
    PolymarketMarketSentiment,
)
from src.services.cache import cache
from src.utils.normalize import to_percentage


class AssetIndicators(BaseModel):
    momentum: float
    trend: float
    volatility: float


class AssetConfidence(BaseModel):
    score: float                      # 0–100
    indicators: AssetIndicators
    raw_data: Dict[str, float]        # e.g. {"latest_price": ..., "return_30d": ...}


class CategoryConfidence(BaseModel):
    score: float                      # 0–100
    assets: Dict[str, AssetConfidence]


class PolymarketSentiment(BaseModel):
    markets: Dict[str, PolymarketMarketSentiment]
    aggregate_sentiment_score: float  # 0–100


class ConfidenceBreakdown(BaseModel):
    overall: float  # 0–100
    categories: Dict[str, CategoryConfidence]
    polymarket_sentiment: PolymarketSentiment



def _compute_asset_score(indicators: Indicators, direction: AssetDirection) -> float:
    """
    Combine normalized indicators into a single per-asset score in [0,100].

    Base formula (0–1):
        raw = 0.5*momentum + 0.3*trend + 0.2*volatility

    Then:
      - For RISK_ON assets: strong = good → use raw as-is.
      - For RISK_OFF assets (hedges like gold, bonds, USD):
          strong = fear/hedge demand → invert (1 - raw).
    """
    raw = (
        0.5 * indicators.momentum
        + 0.3 * indicators.trend
        + 0.2 * indicators.volatility
    )

    # Clamp to [0, 1] just in case
    raw = max(0.0, min(1.0, raw))

    if direction == AssetDirection.RISK_ON:
        effective = raw
    else:  # RISK_OFF
        effective = 1.0 - raw

    return to_percentage(effective)



def _weighted_average(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    total_weight = 0.0
    weighted_sum = 0.0
    for key, score in scores.items():
        w = weights.get(key, 1.0)
        weighted_sum += score * w
        total_weight += w
    if total_weight == 0:
        return 0.0
    return weighted_sum / total_weight


async def build_confidence_breakdown(lookback_days: int = 30) -> ConfidenceBreakdown:
    """
    Main entry point: compute full confidence breakdown for all categories and assets.

    Steps:
    - Pull historical series for each asset.
    - Compute normalized indicators + asset scores.
    - Aggregate to category scores using CATEGORY_WEIGHTS and ASSET_WEIGHTS.
    - Fetch Polymarket sentiment and aggregate into a 0–100 sentiment score.
    - Combine into an overall 0–100 market confidence score, adjusted by sentiment.
    """
    cache_key = f"confidence_breakdown:{lookback_days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    asset_confidences: Dict[str, AssetConfidence] = {}
    category_confidences: Dict[str, CategoryConfidence] = {}

    # 1) Per-asset indicators + scores
    for asset_id, cfg in ASSETS.items():
        series: list[MarketDataPoint] = await get_historical_series(asset_id, lookback_days)
        indicators = compute_indicators(series)
        if indicators is None:
            # Not enough data; treat as neutral score 50
            asset_confidence = AssetConfidence(
                score=50.0,
                indicators=AssetIndicators(momentum=0.5, trend=0.5, volatility=0.5),
                raw_data={"latest_price": series[-1].price if series else 0.0},
            )
        else:
            asset_score = _compute_asset_score(indicators, cfg.direction)
            latest_price = series[-1].price if series else 0.0
            # For now, we store just price; you could add return_30d etc.
            asset_confidence = AssetConfidence(
                score=asset_score,
                indicators=AssetIndicators(
                    momentum=indicators.momentum,
                    trend=indicators.trend,
                    volatility=indicators.volatility,
                ),
                raw_data={"latest_price": latest_price},
            )
        asset_confidences[asset_id] = asset_confidence

    # 2) Aggregate to category scores
    for category, asset_ids in CATEGORY_TO_ASSETS.items():
        scores: Dict[str, float] = {}
        weights_in_cat: Dict[str, float] = {}
        for aid in asset_ids:
            scores[aid] = asset_confidences[aid].score
            weights_in_cat[aid] = ASSET_WEIGHTS.get(aid, None).weight if ASSET_WEIGHTS.get(aid) else 1.0

        cat_score = _weighted_average(scores, weights_in_cat)
        cat_assets = {aid: asset_confidences[aid] for aid in asset_ids}

        category_confidences[category.value] = CategoryConfidence(
            score=cat_score,
            assets=cat_assets,
        )

    # 3) Polymarket sentiment
    

# Inside build_confidence_breakdown, AFTER you have your base/category scores:
    polymarket_sentiment = await get_polymarket_sentiment()
    polymarket_markets = polymarket_sentiment.markets  # Dict[str, PolymarketMarketSentiment]

# Weighted average of probabilities (0–1) -> 0–100
    if polymarket_markets:
        prob_scores: Dict[str, float] = {
            mid: m.probability
            for mid, m in polymarket_markets.items()
        }
        prob_weights: Dict[str, float] = {
            mid: m.impact
            for mid, m in polymarket_markets.items()
        }
        agg_prob_0_1 = _weighted_average(prob_scores, prob_weights)
    else:
        agg_prob_0_1 = 0.5  # neutral if no data

    aggregate_sentiment_score = to_percentage(agg_prob_0_1)

    # Rebuild a clean PolymarketSentiment with our aggregate score
    polymarket_sentiment = PolymarketSentiment(
        markets=polymarket_markets,
        aggregate_sentiment_score=aggregate_sentiment_score,
    )


    # 4) Overall score
    # Base score = weighted average of category scores (0–100)
    cat_score_map: Dict[str, float] = {}
    cat_weight_map: Dict[str, float] = {}
    for cat_enum, cfg in CATEGORY_WEIGHTS.items():
        cat_score_map[cat_enum.value] = category_confidences.get(cat_enum.value, CategoryConfidence(score=50.0, assets={})).score
        cat_weight_map[cat_enum.value] = cfg.weight

    base_overall = _weighted_average(cat_score_map, cat_weight_map)
    '''
    extreme_adjustment = 0.0

    for cat_enum, cfg in CATEGORY_EXTREMES.items():
        cat_key = cat_enum.value
        cat = category_confidences.get(cat_key)
        if not cat:
            continue

        s = cat.score  # 0–100

        # BELOW low_threshold → negative adjustment
        if s < cfg.low_threshold:
            severity = (cfg.low_threshold - s) / cfg.low_threshold  # 0..1
            extreme_adjustment -= severity * cfg.max_negative_adjustment * cfg.weight_factor

        # ABOVE high_threshold → positive adjustment
        elif s > cfg.high_threshold:
            severity = (s - cfg.high_threshold) / (100.0 - cfg.high_threshold)  # 0..1
            extreme_adjustment += severity * cfg.max_positive_adjustment * cfg.weight_factor

    # Apply on top of sentiment-adjusted score, but clamp
    base_overall = max(0.0, min(100.0, overall_score + extreme_adjustment))
    '''
    # Sentiment adjustment: map sentiment (0–100) into [-max_adj, +max_adj]
    # where 50 => 0, >50 => positive, <50 => negative.
    sentiment_deviation = (aggregate_sentiment_score - 50.0) / 50.0  # [-1, 1]
    adjustment = sentiment_deviation * POLYMARKET_WEIGHTS.max_adjustment_points
    # Additionally scale by overall_sentiment_weight (so it doesn't dominate)
    adjustment *= POLYMARKET_WEIGHTS.overall_sentiment_weight
    
    overall_score = max(0.0, min(100.0, base_overall + adjustment))

    breakdown = ConfidenceBreakdown(
        overall=overall_score,
        categories=category_confidences,
        polymarket_sentiment=polymarket_sentiment,
    )

    cache.set(cache_key, breakdown, ttl_seconds=30)  # recompute every 30 seconds
    return breakdown

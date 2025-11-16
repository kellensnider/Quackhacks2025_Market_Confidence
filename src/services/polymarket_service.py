# src/services/polymarket_service.py
from __future__ import annotations

from math import isfinite
from typing import Dict, Optional

from pydantic import BaseModel

from src.config.assets import (
    POLYMARKET_MARKETS,
    PolymarketMarketConfig,
    PolymarketDirection,
)
from src.utils.http import get_json
from src.utils.normalize import normalize_polymarket_probability
from src.services.cache import cache_get, cache_set

import json


class PolymarketMarketSentiment(BaseModel):
    """
    Sentiment for a single Polymarket market.

    probability: 0–1, interpreted as probability of a *good* outcome
                 (after applying direction: POSITIVE/NEGATIVE).
    impact: weight used when aggregating across markets.
    """
    id: str
    name: str
    probability: float
    impact: float


class PolymarketSentiment(BaseModel):
    """
    Aggregate Polymarket sentiment used by the confidence engine.

    markets: individual market sentiments keyed by internal ID.
    aggregate_sentiment_score: 0–100 score representing overall optimism.
    """
    markets: Dict[str, PolymarketMarketSentiment]
    aggregate_sentiment_score: float  # 0–100


GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
POLYMARKET_CACHE_KEY = "polymarket_sentiment"
POLYMARKET_TTL_SECONDS = 60  # seconds


async def _fetch_polymarket_market(
    config: PolymarketMarketConfig,
) -> Optional[PolymarketMarketSentiment]:
    """
    Fetch a single Polymarket market by slug and convert it into a sentiment object.

    Uses the Gamma Markets API:

        GET /markets/slug/{slug}

    Assumptions:
    - Market is binary (Yes/No).
    - `outcomePrices` is a string or list of prices (0–1) for each outcome.
      We treat index 0 as the "YES" / primary outcome.
    - For NEGATIVE direction markets (e.g., "recession"), high probability
      is *bad* for confidence, so we invert (1 - p_yes) to get a "good" probability.
    """
    url = f"{GAMMA_BASE_URL}/markets/slug/{config.slug}"
    #try:
    #    data = await get_json(url)
    #    # Helpful debug logging while developing; you can comment out later.
    #    print(f"[Polymarket] Fetched slug={config.slug}: keys={list(data.keys())}")
    #except Exception as exc:
    #    print(f"[Polymarket] Error fetching {config.slug}: {exc}")
    #    return None
    
    market_data = await get_json(url)
    # outcomePrices can be string or list depending on API version.
    raw = market_data.get("outcomePrices")
    if raw is None:
        print(f"[Polymarket] No outcomePrices for slug={config.slug}")
        return None

    parts = None

    try:
        # CASE 1 — API already returns a real Python list
        if isinstance(raw, list):
            parts = [float(p) for p in raw]

        # CASE 2 — JSON array string, e.g. '["0.415","0.585"]'
        elif isinstance(raw, str):
            s = raw.strip()

            # If it looks like JSON, always parse with json.loads()
            if s.startswith("[") and s.endswith("]"):
                parsed = json.loads(s)
                parts = [float(p) for p in parsed]
            else:
                # LAST RESORT — fallback CSV split
                parts = [float(p.strip()) for p in s.split(",")]

    except Exception as e:
        print(f"[Polymarket] Failed to parse outcomePrices for {config.slug}: {raw!r} ({e})")
        return None

    if not parts or len(parts) == 0:
        print(f"[Polymarket] Empty outcomePrices for {config.slug}")
        return None

    # YES = ALWAYS the FIRST VALUE in EXACT MARKET ORDER
    yes_price = float(parts[0])

    # Clamp to [0, 1] and normalize
    prob_raw = normalize_polymarket_probability(yes_price)

    # Direction handling:
    # - POSITIVE: high prob => good
    # - NEGATIVE: high prob => bad, so we invert.
    if config.direction == PolymarketDirection.NEGATIVE:
        prob_good = 1.0 - prob_raw
    else:
        prob_good = prob_raw

    prob_good = normalize_polymarket_probability(prob_good)

    return PolymarketMarketSentiment(
        id=config.id,
        name=config.name,
        probability=prob_good,
        impact=config.impact_weight,
    )


async def get_polymarket_sentiment() -> PolymarketSentiment:
    """
    Aggregate sentiment across all configured Polymarket markets.

    Returns a PolymarketSentiment with:
      - markets: per-market sentiment
      - aggregate_sentiment_score: weighted average in [0, 100]
    """
    cached = cache_get(POLYMARKET_CACHE_KEY)
    if cached is not None:
        return cached

    markets: Dict[str, PolymarketMarketSentiment] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for market_id, cfg in POLYMARKET_MARKETS.items():
        sentiment = await _fetch_polymarket_market(cfg)
        if not sentiment:
            continue

        markets[market_id] = sentiment

        if isfinite(sentiment.probability) and sentiment.impact > 0:
            weighted_sum += sentiment.probability * sentiment.impact
            total_weight += sentiment.impact

    if total_weight > 0.0:
        aggregate_prob = weighted_sum / total_weight  # 0–1
    else:
        aggregate_prob = 0.5  # neutral if nothing available

    aggregate_score = float(aggregate_prob * 100.0)  # 0–100

    result = PolymarketSentiment(
        markets=markets,
        aggregate_sentiment_score=aggregate_score,
    )

    cache_set(POLYMARKET_CACHE_KEY, result, ttl_seconds=POLYMARKET_TTL_SECONDS)
    return result

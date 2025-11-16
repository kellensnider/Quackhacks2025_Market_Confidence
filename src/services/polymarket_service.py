# src/services/polymarket_service.py
from __future__ import annotations

from typing import Dict, Optional
from pydantic import BaseModel

from src.config.assets import POLYMARKET_MARKETS, PolymarketMarketConfig, PolymarketDirection
from src.services.cache import cache
from src.utils.http import get_json
from src.utils.normalize import normalize_polymarket_probability


class PolymarketMarketSentiment(BaseModel):
    id: str
    name: str
    probability: float  # 0–1 probability of "good" outcome
    impact: float       # impact weight


POLYMARKET_BASE_URL = "https://api.polymarket.com"  # TODO: confirm actual base URL


async def _fetch_polymarket_market(config: PolymarketMarketConfig) -> Optional[PolymarketMarketSentiment]:
    """
    Fetch a single Polymarket market and convert to internal sentiment.

    NOTE: This is a *mocked structure* for the API response. You will likely need
    to adjust the JSON parsing once you confirm the actual Polymarket API.
    """
    # Example: GET /markets/{slug}
    url = f"{POLYMARKET_BASE_URL}/markets/{config.slug}"  # TODO: adjust path
    try:
        data = await get_json(url)
    except Exception:
        # On failure, just return None; caller can handle defaults
        return None

    # ----- MOCKED PARSING -----
    # We'll assume there's a "yes" outcome with a "price" that encodes probability.
    # Adjust keys as needed.
    yes_price = None
    try:
        # This is guessy pseudo-structure:
        outcomes = data.get("outcomes", [])
        for outcome in outcomes:
            if outcome.get("name", "").lower() in ("yes", "up", "recession"):  # tweak logic
                yes_price = float(outcome["price"])
                break
    except Exception:
        yes_price = None

    if yes_price is None:
        return None

    prob_raw = normalize_polymarket_probability(yes_price)

    # If direction is NEGATIVE (e.g. "recession"), we interpret high probability
    # as BAD for confidence, so we invert.
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


async def get_all_polymarket_sentiment() -> Dict[str, PolymarketMarketSentiment]:
    """
    Fetch sentiment for all configured Polymarket markets (with caching).
    """
    cache_key = "polymarket:sentiment"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    results: Dict[str, PolymarketMarketSentiment] = {}
    for market_id, cfg in POLYMARKET_MARKETS.items():
        sentiment = await _fetch_polymarket_market(cfg)
        if sentiment is not None:
            results[market_id] = sentiment

    # Simple fallback: if everything fails, we just return empty.
    cache.set(cache_key, results, ttl_seconds=60)
    return results

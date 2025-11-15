from typing import Dict, List
import httpx
from pydantic import BaseModel

from app.config.polymarket import POLYMARKET_SIGNALS, PolymarketSignalConfig

GAMMA_BASE = "https://gamma-api.polymarket.com"


class PolymarketSignal(BaseModel):
    id: str
    description: str
    impliedProb: float      # 0–1
    rawOutcomePrices: Dict[str, float]


async def _fetch_market_by_slug(slug: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{GAMMA_BASE}/markets/slug/{slug}", timeout=10)
        resp.raise_for_status()
        return resp.json()


def _extract_bullish_prob(market: dict, config: PolymarketSignalConfig) -> PolymarketSignal:
    outcomes_str = market.get("outcomes") or ""
    prices_str = market.get("outcomePrices") or ""

    outcomes = [o.strip() for o in outcomes_str.split(",") if o.strip()]
    prices = [float(p) for p in prices_str.split(",") if p]

    price_map: Dict[str, float] = {}
    for i, outcome in enumerate(outcomes):
        price_map[outcome] = prices[i] if i < len(prices) else 0.0

    bullish = config.bullishOutcome
    implied_prob = price_map.get(bullish, 0.5)  # if missing, default neutral

    return PolymarketSignal(
        id=config.id,
        description=config.description,
        impliedProb=implied_prob,
        rawOutcomePrices=price_map,
    )


async def get_polymarket_signals() -> List[PolymarketSignal]:
    results: List[PolymarketSignal] = []

    for cfg in POLYMARKET_SIGNALS:
        try:
            market = await _fetch_market_by_slug(cfg.slug)
            signal = _extract_bullish_prob(market, cfg)
            results.append(signal)
        except Exception as e:
            print(f"Error fetching Polymarket market {cfg.slug}: {e}")
            # Fallback to neutral signal
            results.append(
                PolymarketSignal(
                    id=cfg.id,
                    description=cfg.description,
                    impliedProb=0.5,
                    rawOutcomePrices={},
                )
            )

    return results

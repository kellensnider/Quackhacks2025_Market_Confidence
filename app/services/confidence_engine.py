from typing import List, Optional
from pydantic import BaseModel
import time

from app.services.market_data_service import get_all_asset_series
from app.services.indicator_service import (
    compute_all_indicators,
    AssetIndicators,
)
from app.services.polymarket_service import (
    get_polymarket_signals,
    PolymarketSignal,
)
from app.config.weights import INDEX_WEIGHTS


class ConfidenceIndexes(BaseModel):
    marketConfidence: float
    riskAppetite: float
    macroStability: float
    timestamp: int
    details: dict


def _find_indicator(
    indicators: List[AssetIndicators], asset_id: str
) -> Optional[AssetIndicators]:
    return next((i for i in indicators if i.assetId == asset_id), None)


def _prob_to_score(p: float) -> float:
    return p * 100.0


async def compute_confidence_indexes() -> ConfidenceIndexes:
    # 1. Pull all data in parallel
    series, poly_signals = await _gather_data()

    # 2. Asset indicators
    indicators = compute_all_indicators(series)

    sp = _find_indicator(indicators, "sp500")
    ndx = _find_indicator(indicators, "nasdaq")
    tech = _find_indicator(indicators, "tech_etf")
    btc = _find_indicator(indicators, "btc")
    gold = _find_indicator(indicators, "gold")
    housing = _find_indicator(indicators, "housing")

    pm_inflation = next((p for p in poly_signals if p.id == "inflation_below_3"), None)
    pm_rates = next((p for p in poly_signals if p.id == "fed_cut_2025"), None)
    pm_equities = next((p for p in poly_signals if p.id == "sp500_green"), None)

    # 3. Market Confidence
    m_w = INDEX_WEIGHTS["marketConfidence"]
    market_confidence = (
        (sp.momentumScore if sp else 50.0) * m_w["sp500Momentum"]
        + (ndx.momentumScore if ndx else 50.0) * m_w["nasdaqMomentum"]
        + (100.0 - (gold.momentumScore if gold else 50.0)) * m_w["gold"]
        + (housing.momentumScore if housing else 50.0) * m_w["housing"]
        + _prob_to_score(pm_inflation.impliedProb if pm_inflation else 0.5)
        * m_w["inflation"]
    )
    market_confidence /= sum(m_w.values())

    # 4. Risk Appetite
    r_w = INDEX_WEIGHTS["riskAppetite"]
    risk_appetite = (
        (ndx.momentumScore if ndx else 50.0) * r_w["nasdaqMomentum"]
        + (tech.momentumScore if tech else 50.0) * r_w["techMomentum"]
        + (btc.momentumScore if btc else 50.0) * r_w["btcMomentum"]
        + _prob_to_score(pm_equities.impliedProb if pm_equities else 0.5)
        * r_w["polymarketEquities"]
    )
    risk_appetite /= sum(r_w.values())

    # 5. Macro Stability
    ms_w = INDEX_WEIGHTS["macroStability"]
    macro_stability = (
        _prob_to_score(pm_inflation.impliedProb if pm_inflation else 0.5)
        * ms_w["inflation"]
        + (housing.momentumScore if housing else 50.0) * ms_w["housing"]
        + _prob_to_score(pm_rates.impliedProb if pm_rates else 0.5)
        * ms_w["polymarketRates"]
        # bondsCurve placeholder — you can add yield curve logic later
    )
    macro_stability /= sum(ms_w.values())

    return ConfidenceIndexes(
        marketConfidence=market_confidence,
        riskAppetite=risk_appetite,
        macroStability=macro_stability,
        timestamp=int(time.time() * 1000),
        details={
            "assets": [i.dict() for i in indicators],
            "polymarket": [s.dict() for s in poly_signals],
        },
    )


async def _gather_data():
    """
    Small helper so we can parallelize external calls later if you want.
    """
    series = await get_all_asset_series()
    poly_signals = await get_polymarket_signals()
    return series, poly_signals

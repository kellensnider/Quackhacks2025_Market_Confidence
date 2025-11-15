from fastapi import APIRouter
from pydantic import BaseModel

from app.services.confidence_engine import compute_confidence_indexes

router = APIRouter(prefix="/api", tags=["confidence"])


class ConfidenceSummary(BaseModel):
    timestamp: int
    marketConfidence: float
    riskAppetite: float
    macroStability: float
    labels: dict


def _to_label(score: float) -> str:
    if score < 20:
        return "Bearish"
    if score < 40:
        return "Weak"
    if score < 60:
        return "Neutral"
    if score < 80:
        return "Confident"
    return "Euphoric"


@router.get("/confidence")
async def get_confidence():
    """
    Full confidence package: indexes + asset + polymarket details.
    """
    data = await compute_confidence_indexes()
    return data


@router.get("/confidence/summary", response_model=ConfidenceSummary)
async def get_confidence_summary():
    """
    Lightweight endpoint for your overview tab.
    """
    data = await compute_confidence_indexes()
    return ConfidenceSummary(
        timestamp=data.timestamp,
        marketConfidence=data.marketConfidence,
        riskAppetite=data.riskAppetite,
        macroStability=data.macroStability,
        labels={
            "marketConfidence": _to_label(data.marketConfidence),
            "riskAppetite": _to_label(data.riskAppetite),
            "macroStability": _to_label(data.macroStability),
        },
    )

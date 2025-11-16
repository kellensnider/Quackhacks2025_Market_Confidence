# src/routes/confidence_routes.py
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.services.confidence_engine import (
    build_confidence_breakdown,
    ConfidenceBreakdown,
)

router = APIRouter(prefix="/confidence", tags=["confidence"])


class OverallResponse(BaseModel):
    overall: float


class CategoriesResponse(BaseModel):
    categories: dict[str, float]


@router.get("/", response_model=ConfidenceBreakdown)
async def get_full_confidence(lookback_days: int = 30):
    """
    Return full confidence breakdown including:
    - overall score
    - per-category scores
    - per-asset scores
    - Polymarket sentiment
    """
    return await build_confidence_breakdown(lookback_days=lookback_days)


@router.get("/overall", response_model=OverallResponse)
async def get_overall_confidence(lookback_days: int = 30):
    breakdown = await build_confidence_breakdown(lookback_days=lookback_days)
    return OverallResponse(overall=breakdown.overall)


@router.get("/categories", response_model=CategoriesResponse)
async def get_category_confidence(lookback_days: int = 30):
    breakdown = await build_confidence_breakdown(lookback_days=lookback_days)
    scores = {name: cat.score for name, cat in breakdown.categories.items()}
    return CategoriesResponse(categories=scores)

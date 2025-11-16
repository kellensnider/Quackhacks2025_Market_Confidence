# src/config/weights.py
from __future__ import annotations

from typing import Dict
from pydantic import BaseModel

from src.config.assets import AssetCategory, ASSETS, POLYMARKET_MARKETS


class AssetWeightConfig(BaseModel):
    asset_id: str
    weight: float  # relative within its category (not necessarily normalized)


class CategoryWeightConfig(BaseModel):
    category: AssetCategory
    weight: float  # relative weight in overall confidence


class PolymarketWeights(BaseModel):
    """
    How Polymarket sentiment feeds into overall confidence.
    """
    # weight of polymarket sentiment vs. other categories (as an extra category)
    overall_sentiment_weight: float = 0.15

    # magnitude of adjustment: e.g., +/- 10 points based on sentiment
    max_adjustment_points: float = 10.0


# Per-asset weights (within each category)
ASSET_WEIGHTS: Dict[str, AssetWeightConfig] = {
    asset_id: AssetWeightConfig(asset_id=asset_id, weight=1.0)
    for asset_id in ASSETS.keys()
}
# You can override defaults, e.g. make BTC more important within crypto:
ASSET_WEIGHTS["btc"] = AssetWeightConfig(asset_id="btc", weight=1.5)

# Per-category weights (in overall score)
CATEGORY_WEIGHTS: Dict[AssetCategory, CategoryWeightConfig] = {
    AssetCategory.EQUITIES: CategoryWeightConfig(
        category=AssetCategory.EQUITIES, weight=0.35
    ),
    AssetCategory.CRYPTO: CategoryWeightConfig(
        category=AssetCategory.CRYPTO, weight=0.20
    ),
    AssetCategory.GOLD: CategoryWeightConfig(
        category=AssetCategory.GOLD, weight=0.10
    ),
    AssetCategory.BONDS: CategoryWeightConfig(
        category=AssetCategory.BONDS, weight=0.10
    ),
    AssetCategory.HOUSING: CategoryWeightConfig(
        category=AssetCategory.HOUSING, weight=0.10
    ),
    AssetCategory.USD: CategoryWeightConfig(
        category=AssetCategory.USD, weight=0.15
    ),
    # Polymarket sentiment is handled separately, see PolymarketWeights
}

POLYMARKET_WEIGHTS = PolymarketWeights()

class CategoryExtremeConfig(BaseModel):
    low_threshold: float = 10.0    # below this → “tank” behavior kicks in
    high_threshold: float = 90.0   # above this → “boost” behavior kicks in
    max_negative_adjustment: float = 8.0  # max points this category can drag
    max_positive_adjustment: float = 8.0  # max points this category can boost
    weight_factor: float = 1.0     # optional: how important this extreme is

CATEGORY_EXTREMES = {
    AssetCategory.HOUSING: CategoryExtremeConfig(
        low_threshold=10.0,
        high_threshold=90.0,
        max_negative_adjustment=10.0,
        max_positive_adjustment=10.0,
        weight_factor=1.2,  # housing extremes matter a bit more
    ),
    AssetCategory.EQUITIES: CategoryExtremeConfig(
        low_threshold=15.0,
        high_threshold=85.0,
        max_negative_adjustment=8.0,
        max_positive_adjustment=6.0,
        weight_factor=1.0,
    ),
    # others if you want, or just leave them out
}

# HOW TO TWEAK:
# - To change the influence of an asset within its category:
#     ASSET_WEIGHTS["spy"].weight = 2.0
# - To change the influence of a whole category in the final score:
#     CATEGORY_WEIGHTS[AssetCategory.CRYPTO].weight = 0.25
# - To change how strongly Polymarket sentiment modifies the final score:
#     POLYMARKET_WEIGHTS.max_adjustment_points = 15.0
#     POLYMARKET_WEIGHTS.overall_sentiment_weight = 0.20

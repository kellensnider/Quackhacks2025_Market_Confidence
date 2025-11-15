from pydantic import BaseModel
from typing import List, Literal


class PolymarketSignalConfig(BaseModel):
    id: str
    slug: str
    description: str
    type: Literal["inflation", "rates", "equities", "recession", "other"]
    bullishOutcome: str = "YES"


POLYMARKET_SIGNALS: List[PolymarketSignalConfig] = [
    PolymarketSignalConfig(
        id="fed_cut_2025",
        slug="fed-cut-rates-in-2025",  # replace with real slug
        description="Probability Fed cuts rates in 2025",
        type="rates",
        bullishOutcome="YES",
    ),
    PolymarketSignalConfig(
        id="inflation_below_3",
        slug="us-inflation-below-3-in-2025",  # replace with real slug
        description="Probability US CPI below 3% by year-end",
        type="inflation",
        bullishOutcome="YES",
    ),
    PolymarketSignalConfig(
        id="sp500_green",
        slug="sp500-up-in-2025",  # replace with real slug
        description="Probability S&P 500 ends the year higher",
        type="equities",
        bullishOutcome="YES",
    ),
]

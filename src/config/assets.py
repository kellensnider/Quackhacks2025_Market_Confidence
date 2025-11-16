# src/config/assets.py
from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, List
from pydantic import BaseModel


class DataSource(str, Enum):
    COINGECKO = "coingecko"
    YFINANCE = "yfinance"
    POLYMARKET = "polymarket"


class AssetCategory(str, Enum):
    EQUITIES = "equities"
    CRYPTO = "crypto"
    GOLD = "gold"
    BONDS = "bonds"
    HOUSING = "housing"
    USD = "usd"
    POLYMARKET_SENTIMENT = "polymarket_sentiment"


class AssetConfig(BaseModel):
    """
    Static configuration for a tradable asset (index ETF, crypto, etc.)
    """
    id: str                       # internal ID, e.g. "spy"
    name: str                     # human-readable, e.g. "S&P 500 (SPY)"
    category: AssetCategory
    data_source: DataSource
    # For CoinGecko-backed assets (crypto)
    coingecko_id: Optional[str] = None
    # For yfinance-backed assets (ETFs / indices / FX proxies)
    yfinance_symbol: Optional[str] = None
    # Optional display order for frontend
    display_order: int = 0


class PolymarketDirection(str, Enum):
    POSITIVE = "positive"  # high probability => higher confidence
    NEGATIVE = "negative"  # high probability => lower confidence


class PolymarketMarketConfig(BaseModel):
    """
    Static configuration for a Polymarket contract we care about.
    """
    id: str                    # internal ID, e.g. "recession_2025"
    name: str                  # human-readable
    slug: str                  # polymarket slug / identifier (approx)
    direction: PolymarketDirection
    impact_weight: float = 1.0      # relative impact in aggregate sentiment


# ---- Asset configuration ----
# NOTE: These are *examples* and can be changed freely.
# We mostly track liquid ETF proxies via yfinance, and BTC via CoinGecko.

ASSETS: Dict[str, AssetConfig] = {
    # Equities
    "spy": AssetConfig(
        id="spy",
        name="S&P 500 (SPY)",
        category=AssetCategory.EQUITIES,
        data_source=DataSource.YFINANCE,
        yfinance_symbol="SPY",
        display_order=1,
    ),
    "qqq": AssetConfig(
        id="qqq",
        name="NASDAQ 100 (QQQ)",
        category=AssetCategory.EQUITIES,
        data_source=DataSource.YFINANCE,
        yfinance_symbol="QQQ",
        display_order=2,
    ),
    "xlk": AssetConfig(
        id="xlk",
        name="Tech Sector (XLK)",
        category=AssetCategory.EQUITIES,
        data_source=DataSource.YFINANCE,
        yfinance_symbol="XLK",
        display_order=3,
    ),
    # Crypto
    "btc": AssetConfig(
        id="btc",
        name="Bitcoin",
        category=AssetCategory.CRYPTO,
        data_source=DataSource.COINGECKO,
        coingecko_id="bitcoin",
        display_order=1,
    ),
    # Defensive / macro
    "gld": AssetConfig(
        id="gld",
        name="Gold (GLD)",
        category=AssetCategory.GOLD,
        data_source=DataSource.YFINANCE,
        yfinance_symbol="GLD",
        display_order=1,
    ),
    "tlt": AssetConfig(
        id="tlt",
        name="US Long-Term Treasuries (TLT)",
        category=AssetCategory.BONDS,
        data_source=DataSource.YFINANCE,
        yfinance_symbol="TLT",
        display_order=1,
    ),
    # Housing
    "xhb": AssetConfig(
        id="xhb",
        name="Housing (XHB)",
        category=AssetCategory.HOUSING,
        data_source=DataSource.YFINANCE,
        yfinance_symbol="XHB",
        display_order=1,
    ),
    # USD / FX
    "uup": AssetConfig(
        id="uup",
        name="US Dollar Index (UUP)",
        category=AssetCategory.USD,
        data_source=DataSource.YFINANCE,
        yfinance_symbol="UUP",
        display_order=1,
    ),
}

# Convenience structure: category -> list of asset ids
CATEGORY_TO_ASSETS: Dict[AssetCategory, List[str]] = {}
for a in ASSETS.values():
    CATEGORY_TO_ASSETS.setdefault(a.category, []).append(a.id)

# ---- Polymarket configuration ----
# Slugs are rough placeholders; adjust to real Polymarket slugs later.

POLYMARKET_MARKETS: Dict[str, PolymarketMarketConfig] = {
    "recession_2025": PolymarketMarketConfig(
        id="bitcoin_today",
        name="Bitcoin Up or Down on November 16?",
        slug="bitcoin-up-or-down-on-november-16",  # TODO: replace with real slug
        direction=PolymarketDirection.POSITIVE,  # higher prob => lower confidence
        impact_weight=1.0,
    )#,
#    "sp500_up_year": PolymarketMarketConfig(
#        id="sp500_up_year",
#        name="S&P 500 Up This Year",
#        slug="sp500-up-this-year",    # TODO: replace with real slug
#        direction=PolymarketDirection.POSITIVE,
#        impact_weight=1.2,
#    ),
#    "major_crash": PolymarketMarketConfig(
#        id="major_crash",
#        name="Major Market Crash",
#        slug="major-market-crash",   # TODO: replace with real slug
#        direction=PolymarketDirection.NEGATIVE,
#        impact_weight=1.5,
#    ),
}

# HOW TO ADD A NEW ASSET:
# 1) Create an AssetConfig entry in ASSETS with:
#    - unique id
#    - name
#    - category (AssetCategory)
#    - data_source (DataSource.COINGECKO or DataSource.YFINANCE)
#    - corresponding coingecko_id or yfinance_symbol
# 2) It will automatically appear in CATEGORY_TO_ASSETS.
#
# HOW TO ADD A NEW POLYMARKET MARKET:
# 1) Add a PolymarketMarketConfig to POLYMARKET_MARKETS.
# 2) Choose direction=POSITIVE if high probability means HIGHER confidence
#    (e.g., "stocks up").
#    Choose direction=NEGATIVE if high probability means LOWER confidence
#    (e.g., "recession", "crash").
# 3) Set impact_weight to control its influence on aggregate sentiment.

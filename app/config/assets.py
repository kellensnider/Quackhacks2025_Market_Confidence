from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class AssetClass(str, Enum):
    equity = "equity"
    crypto = "crypto"
    commodity = "commodity"
    bond = "bond"
    macro = "macro"


class AssetConfig(BaseModel):
    id: str
    name: str
    class_: AssetClass
    source: str               # "yahoo" | "coingecko" | "fred" | "custom"
    symbol: Optional[str] = None
    extra: Dict[str, Any] = {}


ASSETS: List[AssetConfig] = [
    AssetConfig(
        id="sp500",
        name="S&P 500 (SPY)",
        class_=AssetClass.equity,
        source="yfinance",
        symbol="SPY",
    ),
    AssetConfig(
        id="nasdaq",
        name="NASDAQ 100 (QQQ)",
        class_=AssetClass.equity,
        source="yfinance",
        symbol="QQQ",
    ),
    AssetConfig(
        id="tech_etf",
        name="Tech ETF (XLK)",
        class_=AssetClass.equity,
        source="yfinance",
        symbol="XLK",
    ),
    AssetConfig(
        id="gold",
        name="Gold (GLD)",
        class_=AssetClass.commodity,
        source="yfinance",
        symbol="GLD",
    ),
    AssetConfig(
        id="btc",
        name="Bitcoin",
        class_=AssetClass.crypto,
        source="coingecko",
        symbol="bitcoin",
    ),
    AssetConfig(
        id="us10y",
        name="10Y Treasury Yield",
        class_=AssetClass.bond,
        source="fred",
        symbol="DGS10",
    ),
    AssetConfig(
        id="housing",
        name="US Housing Index",
        class_=AssetClass.macro,
        source="fred",
        symbol="CSUSHPINSA",
    ),
    AssetConfig(
        id="cpi",
        name="US CPI YoY",
        class_=AssetClass.macro,
        source="fred",
        symbol="CPIAUCSL",
    ),
]

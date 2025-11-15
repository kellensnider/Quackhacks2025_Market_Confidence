from fastapi import APIRouter

from app.services.market_data_service import get_all_asset_series
from app.services.indicator_service import compute_all_indicators

router = APIRouter(prefix="/api", tags=["assets"])


@router.get("/assets")
async def get_assets():
    """
    Timeseries + indicators for all configured assets.
    """
    series = await get_all_asset_series()
    indicators = compute_all_indicators(series)
    return {
        "series": [s.dict() for s in series],
        "indicators": [i.dict() for i in indicators],
    }

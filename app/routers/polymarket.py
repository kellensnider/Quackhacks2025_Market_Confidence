from fastapi import APIRouter

from app.services.polymarket_service import get_polymarket_signals

router = APIRouter(prefix="/api", tags=["polymarket"])


@router.get("/polymarket/signals")
async def get_polymarket():
    """
    Expose raw polymarket-based probabilities.
    """
    signals = await get_polymarket_signals()
    return [s.dict() for s in signals]

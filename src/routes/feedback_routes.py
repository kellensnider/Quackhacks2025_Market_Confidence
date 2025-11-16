# src/routes/feedback_routes.py
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.feedback_service import add_vote, get_today_stats

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackVote(BaseModel):
    score: float = Field(ge=0, le=100)


class FeedbackStats(BaseModel):
    average: float
    count: int


@router.post("/", status_code=201)
async def submit_feedback(vote: FeedbackVote):
    """Submit a single rating (0–100) for today's date."""
    add_vote(vote.score)
    return {"status": "ok"}


@router.get("/today", response_model=FeedbackStats)
async def get_today_feedback():
    """Get today's crowd average and vote count."""
    stats = get_today_stats()
    return FeedbackStats(**stats)

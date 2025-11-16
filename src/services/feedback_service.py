# src/services/feedback_service.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Dict


@dataclass
class FeedbackBucket:
    sum: float = 0.0
    count: int = 0


# In-memory store: one bucket per calendar day (server's local date)
_feedback_store: Dict[date, FeedbackBucket] = {}


def add_vote(score: float) -> None:
    """Add a single user rating (0–100) for today's date."""
    today = date.today()
    bucket = _feedback_store.setdefault(today, FeedbackBucket())
    bucket.sum += score
    bucket.count += 1


def get_today_stats() -> dict:
    """Return today's aggregate stats: average (0–100) and vote count."""
    today = date.today()
    bucket = _feedback_store.get(today, FeedbackBucket())
    avg = bucket.sum / bucket.count if bucket.count > 0 else 0.0
    return {"average": avg, "count": bucket.count}

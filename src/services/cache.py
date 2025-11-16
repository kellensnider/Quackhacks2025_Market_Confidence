# src/services/cache.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class CacheItem:
    value: Any
    expires_at: float


class SimpleCache:
    """
    Super lightweight in-memory cache.

    NOT multi-process safe; totally fine for a hackathon.
    """

    def __init__(self):
        self._store: Dict[str, CacheItem] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        if item.expires_at < time.time():
            # expired
            self._store.pop(key, None)
            return None
        return item.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = CacheItem(
            value=value,
            expires_at=time.time() + ttl_seconds,
        )

    def clear(self) -> None:
        self._store.clear()


# Single global instance for simplicity
cache = SimpleCache()

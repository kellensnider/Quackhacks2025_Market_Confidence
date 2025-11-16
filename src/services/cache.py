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

_CACHE: Dict[str, Tuple[float, Any]] = {}


def cache_get(key: str) -> Optional[Any]:
    """
    Get a cached value by key.

    Returns:
        - The cached value if present and not expired
        - None if the key is missing or expired
    """
    entry = _CACHE.get(key)
    if entry is None:
        return None

    expires_at, value = entry
    now = time.time()
    if expires_at < now:
        # Expired: remove and return None
        _CACHE.pop(key, None)
        return None

    return value


def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    """
    Store a value in the cache with a time-to-live in seconds.
    """
    expires_at = time.time() + float(ttl_seconds)
    _CACHE[key] = (expires_at, value)


def cache_clear() -> None:
    """
    Clear all entries from the cache.
    Useful in tests or if you want to force a reset.
    """
    _CACHE.clear()
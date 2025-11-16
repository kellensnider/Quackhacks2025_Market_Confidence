# src/utils/http.py
from __future__ import annotations

from typing import Any, Optional
import httpx


class HTTPError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


async def get_json(
    url: str,
    timeout_seconds: float = 5.0,
    params: Optional[dict[str, Any]] = None,
) -> Any:
    """
    Perform a simple HTTP GET and return JSON.

    Raises:
        HTTPError if request fails or response is non-2xx.
    """
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        try:
            resp = await client.get(url, params=params)
        except httpx.RequestError as exc:
            raise HTTPError(f"HTTP request error: {exc}") from exc

        if resp.status_code // 100 != 2:
            raise HTTPError(
                f"HTTP {resp.status_code} from {url}: {resp.text}",
                status_code=resp.status_code,
            )
        return resp.json()

from cachetools import TTLCache
import asyncio
import logging
from datetime import datetime
from typing import Optional, Any

logger = logging.getLogger(__name__)

# TTL values in seconds
TTL_PRICE_DATA      = 5 * 60       # 5 minutes
TTL_COMPANY_OVERVIEW = 24 * 60 * 60 # 24 hours
TTL_FINANCIALS      = 12 * 60 * 60  # 12 hours
TTL_NEWS            = 15 * 60       # 15 minutes

class CacheService:
    """
    Central cache for all provider responses.
    Keys follow pattern: {data_type}:{ticker}
    e.g. "price_history:AAPL", "company_overview:TSLA"

    Structured to be swappable with Redis later — just replace
    the get/set methods with Redis calls.
    """

    def __init__(self):
        self._price_cache    = TTLCache(maxsize=200, ttl=TTL_PRICE_DATA)
        self._overview_cache = TTLCache(maxsize=500, ttl=TTL_COMPANY_OVERVIEW)
        self._financial_cache = TTLCache(maxsize=300, ttl=TTL_FINANCIALS)
        self._news_cache     = TTLCache(maxsize=200, ttl=TTL_NEWS)
        self._lock = asyncio.Lock()

    def _get_cache(self, data_type: str) -> TTLCache:
        return {
            "price_history":     self._price_cache,
            "company_overview":  self._overview_cache,
            "income_statement":  self._financial_cache,
            "balance_sheet":     self._financial_cache,
            "cash_flow":         self._financial_cache,
            "news":              self._news_cache,
        }.get(data_type, self._overview_cache)

    async def get(self, data_type: str, ticker: str) -> Optional[Any]:
        key = f"{data_type}:{ticker.upper()}"
        async with self._lock:
            value = self._get_cache(data_type).get(key)
            if value:
                logger.debug(f"[Cache] HIT {key}")
                return value
            logger.debug(f"[Cache] MISS {key}")
            return None

    async def set(self, data_type: str, ticker: str, value: Any) -> None:
        key = f"{data_type}:{ticker.upper()}"
        async with self._lock:
            self._get_cache(data_type)[key] = value
            logger.debug(f"[Cache] SET {key}")

    async def invalidate(self, data_type: str, ticker: str) -> None:
        key = f"{data_type}:{ticker.upper()}"
        async with self._lock:
            cache = self._get_cache(data_type)
            if key in cache:
                del cache[key]
                logger.info(f"[Cache] INVALIDATED {key}")

    def stats(self) -> dict:
        return {
            "price_cache":    {"size": len(self._price_cache),    "maxsize": self._price_cache.maxsize},
            "overview_cache": {"size": len(self._overview_cache), "maxsize": self._overview_cache.maxsize},
            "financial_cache":{"size": len(self._financial_cache),"maxsize": self._financial_cache.maxsize},
            "news_cache":     {"size": len(self._news_cache),     "maxsize": self._news_cache.maxsize},
        }

# Global singleton — import this everywhere
cache_service = CacheService()

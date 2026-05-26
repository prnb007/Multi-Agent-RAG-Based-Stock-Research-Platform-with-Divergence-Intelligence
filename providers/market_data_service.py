"""
MarketDataService — the ONLY import agents should ever use.
Combines ProviderRouter + CacheService into one clean interface.

Usage in any agent:
    from providers.market_data_service import market_data_service
    overview = await market_data_service.get_company_overview("AAPL")
"""

import logging
from providers.provider_router import ProviderRouter
from providers.cache_service import cache_service
from providers.models import (
    CompanyOverview, PriceHistory,
    IncomeStatement, BalanceSheet, CashFlowStatement, NewsItem
)

logger = logging.getLogger(__name__)


class MarketDataService:

    def __init__(self):
        self._router = ProviderRouter()

    async def get_company_overview(self, ticker: str) -> CompanyOverview:
        cached = await cache_service.get("company_overview", ticker)
        if cached:
            return cached
        result = await self._router.fetch("get_company_overview", ticker)
        await cache_service.set("company_overview", ticker, result)
        return result

    async def get_price_history(self, ticker: str) -> PriceHistory:
        cached = await cache_service.get("price_history", ticker)
        if cached:
            return cached
        result = await self._router.fetch("get_price_history", ticker)
        await cache_service.set("price_history", ticker, result)
        return result

    async def get_income_statement(self, ticker: str) -> IncomeStatement:
        cached = await cache_service.get("income_statement", ticker)
        if cached:
            return cached
        result = await self._router.fetch("get_income_statement", ticker)
        await cache_service.set("income_statement", ticker, result)
        return result

    async def get_balance_sheet(self, ticker: str) -> BalanceSheet:
        cached = await cache_service.get("balance_sheet", ticker)
        if cached:
            return cached
        result = await self._router.fetch("get_balance_sheet", ticker)
        await cache_service.set("balance_sheet", ticker, result)
        return result

    async def get_cash_flow(self, ticker: str) -> CashFlowStatement:
        cached = await cache_service.get("cash_flow", ticker)
        if cached:
            return cached
        result = await self._router.fetch("get_cash_flow", ticker)
        await cache_service.set("cash_flow", ticker, result)
        return result

    async def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
        cached = await cache_service.get("news", ticker)
        if cached:
            return cached
        result = await self._router.fetch("get_news", ticker, limit=limit)
        await cache_service.set("news", ticker, result)
        return result


# Global singleton — import this everywhere
market_data_service = MarketDataService()

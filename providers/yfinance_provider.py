"""
YFinanceProvider — Fallback provider only.
Used when Alpha Vantage fails, times out, or hits rate limits.
Returns same normalized models as AlphaVantageProvider.
"""

import logging
import time
import yfinance as yf
import requests
from datetime import datetime
from typing import Optional

from providers.models import (
    CompanyOverview, PriceHistory, PricePoint,
    IncomeStatement, BalanceSheet, CashFlowStatement, NewsItem
)
from providers.retry_service import standard_retry, aggressive_retry

logger = logging.getLogger(__name__)

# Browser-like session to reduce 429s
_session = requests.Session()
_session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
})


class YFinanceProvider:
    """
    Fallback provider using yfinance.
    Returns same normalized models as AlphaVantageProvider.
    """

    def __init__(self):
        self.name = "yfinance"

    def _ticker(self, symbol: str):
        return yf.Ticker(symbol)

    @standard_retry
    async def get_company_overview(self, ticker: str) -> CompanyOverview:
        logger.info(f"[YF] Fetching overview for {ticker} (fallback)")
        import asyncio
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, lambda: self._ticker(ticker).info
        )
        if not info or "shortName" not in info:
            raise ValueError(f"yfinance returned empty info for {ticker}")

        def sf(key): return info.get(key) or None

        return CompanyOverview(
            ticker=ticker.upper(),
            name=info.get("longName") or info.get("shortName", ticker),
            sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"),
            description=info.get("longBusinessSummary"),
            market_cap=sf("marketCap"),
            pe_ratio=sf("trailingPE"),
            forward_pe=sf("forwardPE"),
            price_to_book=sf("priceToBook"),
            debt_to_equity=sf("debtToEquity"),
            return_on_equity=sf("returnOnEquity"),
            revenue_growth=sf("revenueGrowth"),
            earnings_growth=sf("earningsGrowth"),
            current_price=sf("currentPrice") or sf("regularMarketPrice"),
            fifty_two_week_high=sf("fiftyTwoWeekHigh"),
            fifty_two_week_low=sf("fiftyTwoWeekLow"),
            dividend_yield=sf("dividendYield"),
            beta=sf("beta"),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @aggressive_retry
    async def get_price_history(self, ticker: str) -> PriceHistory:
        logger.info(f"[YF] Fetching price history for {ticker} (fallback)")
        import asyncio
        loop = asyncio.get_event_loop()
        hist = await loop.run_in_executor(
            None, lambda: self._ticker(ticker).history(period="6mo")
        )
        if hist.empty:
            raise ValueError(f"yfinance returned empty price history for {ticker}")

        points = []
        for date, row in hist.iterrows():
            try:
                points.append(PricePoint(
                    date=str(date.date()),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                ))
            except Exception:
                continue

        return PriceHistory(
            ticker=ticker.upper(),
            interval="daily",
            points=sorted(points, key=lambda p: p.date, reverse=True),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @standard_retry
    async def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
        import asyncio
        loop = asyncio.get_event_loop()
        news = await loop.run_in_executor(
            None, lambda: self._ticker(ticker).news or []
        )
        items = []
        for item in news[:limit]:
            try:
                items.append(NewsItem(
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    url=item.get("link", ""),
                    source=item.get("publisher", "Yahoo Finance"),
                    published_at=datetime.fromtimestamp(
                        item.get("providerPublishTime", 0)
                    ).isoformat(),
                    sentiment_score=None,
                    provider=self.name,
                    fetched_at=datetime.utcnow()
                ))
            except Exception:
                continue
        return items

    @standard_retry
    async def get_income_statement(self, ticker: str) -> IncomeStatement:
        return IncomeStatement(
            ticker=ticker.upper(),
            fiscal_year=str(datetime.utcnow().year),
            total_revenue=None,
            gross_profit=None,
            operating_income=None,
            net_income=None,
            ebitda=None,
            eps=None,
            research_development=None,
            reported_date=str(datetime.utcnow().date()),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @standard_retry
    async def get_balance_sheet(self, ticker: str) -> BalanceSheet:
        return BalanceSheet(
            ticker=ticker.upper(),
            fiscal_year=str(datetime.utcnow().year),
            total_assets=None,
            total_liabilities=None,
            total_equity=None,
            total_debt=None,
            cash_and_equivalents=None,
            current_ratio=None,
            reported_date=str(datetime.utcnow().date()),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @standard_retry
    async def get_cash_flow(self, ticker: str) -> CashFlowStatement:
        return CashFlowStatement(
            ticker=ticker.upper(),
            fiscal_year=str(datetime.utcnow().year),
            operating_cash_flow=None,
            free_cash_flow=None,
            capital_expenditures=None,
            dividends_paid=None,
            reported_date=str(datetime.utcnow().date()),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

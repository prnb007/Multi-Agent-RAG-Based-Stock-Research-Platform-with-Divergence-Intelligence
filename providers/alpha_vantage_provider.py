"""
AlphaVantageProvider — Primary data provider.
Uses httpx.AsyncClient for all calls.
Returns normalized models from providers/models.py.
NEVER returns raw API JSON to callers.
"""

import os
import logging
import httpx
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from providers.models import (
    CompanyOverview, PriceHistory, PricePoint,
    IncomeStatement, BalanceSheet, CashFlowStatement,
    NewsItem, ProviderError
)
from providers.retry_service import standard_retry, aggressive_retry, light_retry

load_dotenv()
logger = logging.getLogger(__name__)

AV_BASE = "https://www.alphavantage.co/query"
AV_KEY  = os.getenv("ALPHA_VANTAGE_KEY", "")


class AlphaVantageProvider:
    """
    Fetches and normalizes data from Alpha Vantage API.
    All methods return normalized Pydantic models — never raw dicts.
    """

    def __init__(self):
        self.name = "alpha_vantage"
        self._client = httpx.AsyncClient(timeout=15.0)

    async def _get(self, params: dict) -> dict:
        params["apikey"] = AV_KEY
        response = await self._client.get(AV_BASE, params=params)
        response.raise_for_status()
        data = response.json()
        if "Note" in data or "Information" in data:
            raise httpx.HTTPStatusError(
                "Rate limit hit",
                request=response.request,
                response=response
            )
        return data

    @aggressive_retry
    async def get_company_overview(self, ticker: str) -> CompanyOverview:
        logger.info(f"[AV] Fetching overview for {ticker}")
        start = __import__("time").time()
        data = await self._get({"function": "OVERVIEW", "symbol": ticker})

        if not data or "Symbol" not in data:
            raise ValueError(f"Empty overview response for {ticker}")

        def safe_float(val) -> Optional[float]:
            try:
                return float(val) if val and val != "None" and val != "-" else None
            except (ValueError, TypeError):
                return None

        return CompanyOverview(
            ticker=ticker.upper(),
            name=data.get("Name", ticker),
            sector=data.get("Sector", "Unknown"),
            industry=data.get("Industry", "Unknown"),
            description=data.get("Description"),
            market_cap=safe_float(data.get("MarketCapitalization")),
            pe_ratio=safe_float(data.get("TrailingPE")),
            forward_pe=safe_float(data.get("ForwardPE")),
            price_to_book=safe_float(data.get("PriceToBookRatio")),
            debt_to_equity=safe_float(data.get("DebtToEquityRatio")),
            return_on_equity=safe_float(data.get("ReturnOnEquityTTM")),
            revenue_growth=safe_float(data.get("QuarterlyRevenueGrowthYOY")),
            earnings_growth=safe_float(data.get("QuarterlyEarningsGrowthYOY")),
            current_price=safe_float(data.get("50DayMovingAverage")),
            fifty_two_week_high=safe_float(data.get("52WeekHigh")),
            fifty_two_week_low=safe_float(data.get("52WeekLow")),
            dividend_yield=safe_float(data.get("DividendYield")),
            beta=safe_float(data.get("Beta")),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @aggressive_retry
    async def get_price_history(self, ticker: str) -> PriceHistory:
        logger.info(f"[AV] Fetching price history for {ticker}")
        data = await self._get({
            "function": "TIME_SERIES_DAILY",
            "symbol": ticker,
            "outputsize": "compact"
        })

        ts = data.get("Time Series (Daily)", {})
        if not ts:
            raise ValueError(f"No price data in AV response for {ticker}")

        points = []
        for date_str, values in sorted(ts.items(), reverse=True)[:180]:
            try:
                points.append(PricePoint(
                    date=date_str,
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    volume=int(values["5. volume"]),
                ))
            except (KeyError, ValueError):
                continue

        if not points:
            raise ValueError(f"Failed to parse price points for {ticker}")

        return PriceHistory(
            ticker=ticker.upper(),
            interval="daily",
            points=points,
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @standard_retry
    async def get_income_statement(self, ticker: str) -> Optional[IncomeStatement]:
        logger.info(f"[AV] Fetching income statement for {ticker}")
        data = await self._get({"function": "INCOME_STATEMENT", "symbol": ticker})
        reports = data.get("annualReports", [])
        if not reports:
            return None
        r = reports[0]

        def sf(v): return float(v) if v and v != "None" else None

        return IncomeStatement(
            ticker=ticker.upper(),
            fiscal_year=r.get("fiscalDateEnding", ""),
            total_revenue=sf(r.get("totalRevenue")),
            gross_profit=sf(r.get("grossProfit")),
            operating_income=sf(r.get("operatingIncome")),
            net_income=sf(r.get("netIncome")),
            ebitda=sf(r.get("ebitda")),
            eps=sf(r.get("reportedEPS")),
            research_development=sf(r.get("researchAndDevelopment")),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @standard_retry
    async def get_balance_sheet(self, ticker: str) -> Optional[BalanceSheet]:
        logger.info(f"[AV] Fetching balance sheet for {ticker}")
        data = await self._get({"function": "BALANCE_SHEET", "symbol": ticker})
        reports = data.get("annualReports", [])
        if not reports:
            return None
        r = reports[0]
        def sf(v): return float(v) if v and v != "None" else None

        total_assets = sf(r.get("totalAssets"))
        total_liabilities = sf(r.get("totalLiabilities"))
        current_assets = sf(r.get("totalCurrentAssets"))
        current_liabilities = sf(r.get("totalCurrentLiabilities"))
        current_ratio = (
            current_assets / current_liabilities
            if current_assets and current_liabilities and current_liabilities != 0
            else None
        )

        return BalanceSheet(
            ticker=ticker.upper(),
            fiscal_year=r.get("fiscalDateEnding", ""),
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=sf(r.get("totalShareholderEquity")),
            cash_and_equivalents=sf(r.get("cashAndCashEquivalentsAtCarryingValue")),
            total_debt=sf(r.get("longTermDebt")),
            current_ratio=current_ratio,
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @standard_retry
    async def get_cash_flow(self, ticker: str) -> Optional[CashFlowStatement]:
        logger.info(f"[AV] Fetching cash flow for {ticker}")
        data = await self._get({"function": "CASH_FLOW", "symbol": ticker})
        reports = data.get("annualReports", [])
        if not reports:
            return None
        r = reports[0]
        def sf(v): return float(v) if v and v != "None" else None

        operating_cf = sf(r.get("operatingCashflow"))
        capex = sf(r.get("capitalExpenditures"))
        free_cf = (
            operating_cf - abs(capex)
            if operating_cf is not None and capex is not None
            else None
        )

        return CashFlowStatement(
            ticker=ticker.upper(),
            fiscal_year=r.get("fiscalDateEnding", ""),
            operating_cash_flow=operating_cf,
            capital_expenditures=capex,
            free_cash_flow=free_cf,
            dividends_paid=sf(r.get("dividendPayout")),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    @light_retry
    async def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
        logger.info(f"[AV] Fetching news for {ticker}")
        data = await self._get({
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "limit": limit
        })
        items = []
        for article in data.get("feed", []):
            try:
                sentiment = None
                for ts in article.get("ticker_sentiment", []):
                    if ts.get("ticker") == ticker:
                        sentiment = float(ts.get("ticker_sentiment_score", 0))
                items.append(NewsItem(
                    title=article.get("title", ""),
                    summary=article.get("summary"),
                    url=article.get("url", ""),
                    source=article.get("source", ""),
                    published_at=article.get("time_published", ""),
                    sentiment_score=sentiment,
                    provider=self.name,
                    fetched_at=datetime.utcnow()
                ))
            except Exception:
                continue
        return items

    async def close(self):
        await self._client.aclose()

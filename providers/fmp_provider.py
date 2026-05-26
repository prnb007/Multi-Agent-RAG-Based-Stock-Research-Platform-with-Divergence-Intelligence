"""
FMPProvider — Primary provider for fundamentals:
  - Complete company overview (profile + quote + key metrics combined)
  - Annual income statement
  - Annual balance sheet
  - Annual cash flow statement

Returns normalized models from providers/models.py.
Uses httpx.AsyncClient for async calls.
Free tier: 250 calls/day — caching is critical.
"""

import os
import logging
import httpx
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from providers.models import (
    CompanyOverview, IncomeStatement,
    BalanceSheet, CashFlowStatement
)
from providers.retry_service import standard_retry, aggressive_retry

load_dotenv()
logger = logging.getLogger(__name__)

FMP_BASE = "https://financialmodelingprep.com/stable"
FMP_KEY  = os.getenv("FMP_API_KEY", "")


class FMPProvider:
    """
    Financial Modeling Prep data provider.
    Primary source for fundamentals — superior to Finnhub for financial statements.
    """

    def __init__(self):
        self.name = "fmp"
        self._client = httpx.AsyncClient(timeout=15.0)

    async def _get(self, endpoint: str, params: dict = None) -> dict | list:
        if params is None:
            params = {}
        params["apikey"] = FMP_KEY
        url = f"{FMP_BASE}{endpoint}"
        response = await self._client.get(url, params=params)
        if response.status_code == 429:
            raise httpx.HTTPStatusError(
                "FMP rate limit hit",
                request=response.request,
                response=response
            )
        response.raise_for_status()
        data = response.json()
        # FMP returns error messages as dicts with "Error Message" key
        if isinstance(data, dict) and "Error Message" in data:
            raise ValueError(f"FMP API error: {data['Error Message']}")
        return data

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _safe_float(val) -> Optional[float]:
        try:
            return float(val) if val is not None and val != 0 else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _first_or_none(data) -> Optional[dict]:
        """FMP statement endpoints return a list — get the most recent entry."""
        if isinstance(data, list) and data:
            return data[0]
        return None

    # ------------------------------------------------------------------
    # Company overview — the BIG one, combines 3 endpoints
    # ------------------------------------------------------------------
    @standard_retry
    async def get_company_overview(self, ticker: str) -> CompanyOverview:
        """
        Combines /profile + /quote + /key-metrics into one normalized overview.
        Costs 3 API calls per ticker but the cache makes this fine.
        """
        logger.info(f"[FMP] Fetching company overview for {ticker}")

        profile_list = await self._get("/profile", {"symbol": ticker})
        profile = self._first_or_none(profile_list)
        if not profile:
            raise ValueError(f"FMP returned empty profile for {ticker}")

        # Fetch quote and key metrics in parallel
        import asyncio
        quote_data, metrics_data = await asyncio.gather(
            self._get("/quote", {"symbol": ticker}),
            self._get("/key-metrics", {"symbol": ticker, "limit": 1, "period": "annual"}),
            return_exceptions=True,
        )

        quote   = self._first_or_none(quote_data)   if not isinstance(quote_data,   Exception) else None
        metrics = self._first_or_none(metrics_data) if not isinstance(metrics_data, Exception) else None

        # Try /financial-growth for revenue + earnings growth
        try:
            growth_data = await self._get(
                "/financial-growth",
                {"symbol": ticker, "limit": 1, "period": "annual"}
            )
            growth = self._first_or_none(growth_data)
        except Exception:
            growth = None

        sf = self._safe_float

        # Fallback: compute valuation metrics from financials if FMP free tier didn't return them
        derived_pe          = None
        derived_roe         = None
        derived_market_cap  = None
        derived_pb          = None
        derived_de          = None

        try:
            # Fetch income + balance in parallel — needed to derive missing metrics
            income_data, balance_data = await asyncio.gather(
                self._get("/income-statement", {"symbol": ticker, "limit": 1, "period": "annual"}),
                self._get("/balance-sheet-statement", {"symbol": ticker, "limit": 1, "period": "annual"}),
                return_exceptions=True,
            )
            income  = self._first_or_none(income_data)  if not isinstance(income_data,  Exception) else None
            balance = self._first_or_none(balance_data) if not isinstance(balance_data, Exception) else None

            current_price = sf(profile.get("price"))

            # 1. P/E = current_price / EPS
            if current_price and income and income.get("eps"):
                eps = sf(income.get("eps"))
                if eps and eps > 0:
                    derived_pe = round(current_price / eps, 2)

            # 2. ROE = net_income / total_equity
            if income and balance:
                net_income = sf(income.get("netIncome"))
                equity     = sf(balance.get("totalStockholdersEquity"))
                if net_income and equity and equity > 0:
                    derived_roe = round(net_income / equity, 4)

            # 3. Market cap = current_price × weightedAverageShsOut
            if current_price and income and income.get("weightedAverageShsOut"):
                shares = sf(income.get("weightedAverageShsOut"))
                if shares and shares > 0:
                    derived_market_cap = round(current_price * shares, 2)

            # 4. P/B = market_cap / total_equity
            if derived_market_cap and balance:
                equity = sf(balance.get("totalStockholdersEquity"))
                if equity and equity > 0:
                    derived_pb = round(derived_market_cap / equity, 2)

            # 5. D/E = total_debt / total_equity
            if balance:
                total_debt = sf(balance.get("totalDebt"))
                equity     = sf(balance.get("totalStockholdersEquity"))
                if total_debt and equity and equity > 0:
                    derived_de = round(total_debt / equity, 4)

        except Exception as e:
            logger.warning(f"[FMP] Could not derive metrics for {ticker}: {e}")

        return CompanyOverview(
            ticker=ticker.upper(),
            name=profile.get("companyName", ticker),
            sector=(profile.get("sector") or "Unknown").upper(),
            industry=profile.get("industry", "Unknown"),
            description=profile.get("description"),
            market_cap=sf(profile.get("mktCap")) or derived_market_cap,
            pe_ratio=(sf(quote.get("pe")) if quote else None) or derived_pe,
            forward_pe=None,
            price_to_book=(sf(metrics.get("pbRatio")) if metrics else None) or derived_pb,
            debt_to_equity=(sf(metrics.get("debtToEquity")) if metrics else None) or derived_de,
            return_on_equity=(sf(metrics.get("roe")) if metrics else None) or derived_roe,
            revenue_growth=sf(growth.get("revenueGrowth")) if growth else None,
            earnings_growth=sf(growth.get("netIncomeGrowth")) if growth else None,
            current_price=sf(profile.get("price")),
            fifty_two_week_high=sf(quote.get("yearHigh")) if quote else None,
            fifty_two_week_low=sf(quote.get("yearLow")) if quote else None,
            dividend_yield=sf(profile.get("lastDiv")),
            beta=sf(profile.get("beta")),
            provider=self.name,
            fetched_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Income statement
    # ------------------------------------------------------------------
    @standard_retry
    async def get_income_statement(self, ticker: str) -> Optional[IncomeStatement]:
        logger.info(f"[FMP] Fetching income statement for {ticker}")
        data = await self._get(
            "/income-statement",
            {"symbol": ticker, "limit": 1, "period": "annual"}
        )
        r = self._first_or_none(data)
        if not r:
            return None

        sf = self._safe_float
        return IncomeStatement(
            ticker=ticker.upper(),
            fiscal_year=r.get("calendarYear") or r.get("date", ""),
            total_revenue=sf(r.get("revenue")),
            gross_profit=sf(r.get("grossProfit")),
            operating_income=sf(r.get("operatingIncome")),
            net_income=sf(r.get("netIncome")),
            ebitda=sf(r.get("ebitda")),
            eps=sf(r.get("eps")),
            research_development=sf(r.get("researchAndDevelopmentExpenses")),
            provider=self.name,
            fetched_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Balance sheet
    # ------------------------------------------------------------------
    @standard_retry
    async def get_balance_sheet(self, ticker: str) -> Optional[BalanceSheet]:
        logger.info(f"[FMP] Fetching balance sheet for {ticker}")
        data = await self._get(
            "/balance-sheet-statement",
            {"symbol": ticker, "limit": 1, "period": "annual"}
        )
        r = self._first_or_none(data)
        if not r:
            return None

        sf = self._safe_float
        current_assets = sf(r.get("totalCurrentAssets"))
        current_liabs  = sf(r.get("totalCurrentLiabilities"))
        current_ratio = (
            current_assets / current_liabs
            if current_assets and current_liabs and current_liabs != 0
            else None
        )

        return BalanceSheet(
            ticker=ticker.upper(),
            fiscal_year=r.get("calendarYear") or r.get("date", ""),
            total_assets=sf(r.get("totalAssets")),
            total_liabilities=sf(r.get("totalLiabilities")),
            total_equity=sf(r.get("totalStockholdersEquity")),
            cash_and_equivalents=sf(r.get("cashAndCashEquivalents")),
            total_debt=sf(r.get("totalDebt")),
            current_ratio=round(current_ratio, 3) if current_ratio else None,
            provider=self.name,
            fetched_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Cash flow statement
    # ------------------------------------------------------------------
    @standard_retry
    async def get_cash_flow(self, ticker: str) -> Optional[CashFlowStatement]:
        logger.info(f"[FMP] Fetching cash flow for {ticker}")
        data = await self._get(
            "/cash-flow-statement",
            {"symbol": ticker, "limit": 1, "period": "annual"}
        )
        r = self._first_or_none(data)
        if not r:
            return None

        sf = self._safe_float
        operating_cf = sf(r.get("operatingCashFlow"))
        capex        = sf(r.get("capitalExpenditure"))

        # FMP reports capex as negative, so we add it (subtracting absolute value)
        free_cf = (
            operating_cf + capex
            if operating_cf is not None and capex is not None
            else sf(r.get("freeCashFlow"))
        )

        return CashFlowStatement(
            ticker=ticker.upper(),
            fiscal_year=r.get("calendarYear") or r.get("date", ""),
            operating_cash_flow=operating_cf,
            capital_expenditures=capex,
            free_cash_flow=free_cf,
            dividends_paid=sf(r.get("dividendsPaid")),
            provider=self.name,
            fetched_at=datetime.utcnow(),
        )

    async def close(self):
        await self._client.aclose()

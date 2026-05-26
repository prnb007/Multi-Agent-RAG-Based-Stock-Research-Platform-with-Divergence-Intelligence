from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CompanyOverview(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    description: Optional[str]
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    forward_pe: Optional[float]
    price_to_book: Optional[float]
    debt_to_equity: Optional[float]
    return_on_equity: Optional[float]
    revenue_growth: Optional[float]
    earnings_growth: Optional[float]
    current_price: Optional[float]
    fifty_two_week_high: Optional[float]
    fifty_two_week_low: Optional[float]
    dividend_yield: Optional[float]
    beta: Optional[float]
    provider: str    # which provider returned this: "alpha_vantage" | "yfinance"
    fetched_at: datetime

class PricePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class PriceHistory(BaseModel):
    ticker: str
    interval: str     # "daily" | "weekly"
    points: list[PricePoint]
    provider: str
    fetched_at: datetime

class IncomeStatement(BaseModel):
    ticker: str
    fiscal_year: str
    total_revenue: Optional[float]
    gross_profit: Optional[float]
    operating_income: Optional[float]
    net_income: Optional[float]
    ebitda: Optional[float]
    eps: Optional[float]
    research_development: Optional[float]
    provider: str
    fetched_at: datetime

class BalanceSheet(BaseModel):
    ticker: str
    fiscal_year: str
    total_assets: Optional[float]
    total_liabilities: Optional[float]
    total_equity: Optional[float]
    cash_and_equivalents: Optional[float]
    total_debt: Optional[float]
    current_ratio: Optional[float]
    provider: str
    fetched_at: datetime

class CashFlowStatement(BaseModel):
    ticker: str
    fiscal_year: str
    operating_cash_flow: Optional[float]
    capital_expenditures: Optional[float]
    free_cash_flow: Optional[float]
    dividends_paid: Optional[float]
    provider: str
    fetched_at: datetime

class NewsItem(BaseModel):
    title: str
    summary: Optional[str]
    url: str
    source: str
    published_at: str
    sentiment_score: Optional[float]   # -1.0 to 1.0 if provider gives it
    provider: str
    fetched_at: datetime

class ProviderError(BaseModel):
    provider: str
    error_type: str    # "rate_limit" | "timeout" | "not_found" | "parse_error" | "unknown"
    message: str
    timestamp: datetime
    ticker: Optional[str]

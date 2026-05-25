from pydantic import BaseModel
from typing import Optional


# ── Raw data shapes ──────────────────────────────────────────────

class StockInfo(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
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
    description: Optional[str]


class NewsArticle(BaseModel):
    title: str
    description: Optional[str]
    content: Optional[str]
    url: str
    published_at: str
    source: str


class InsiderTrade(BaseModel):
    filer_name: str
    transaction_type: str   # "Buy" or "Sell"
    shares: float
    price_per_share: Optional[float]
    date: str


# ── Agent output — every agent returns this exact shape ──────────

class AgentOutput(BaseModel):
    agent: str                  # "fundamentals" | "sentiment" | "insider" | "technical" | "macro"
    score: float                # -1.0 (very bearish) to +1.0 (very bullish)
    confidence: float           # 0.0 to 1.0
    summary: str                # 2-3 sentence plain-English summary
    evidence: list[str]         # bullet points backing the score
    raw_data: Optional[dict] = None  # optional extra context


# ── Synthesis / final report ─────────────────────────────────────

class DivergenceAlert(BaseModel):
    agent_a: str
    agent_b: str
    score_a: float
    score_b: float
    gap: float                  # abs(score_a - score_b)
    explanation: str


class FinalReport(BaseModel):
    ticker: str
    company_name: str
    generated_at: str
    agents: list[AgentOutput]
    divergence_score: float     # 0.0 (all agree) to 1.0 (maximum conflict)
    divergence_alerts: list[DivergenceAlert]
    bull_thesis: str
    bear_thesis: str
    overall_score: float        # weighted average of agent scores
    confidence: float           # average confidence

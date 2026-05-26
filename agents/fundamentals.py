"""
FundamentalsAgent
Uses FinancialAnalysisService for derived metrics.
Uses MarketDataService for raw statements.
NEVER calls yfinance, requests, or any provider directly.
"""

import logging
from agents.base import AgentOutput, call_llm
from providers.market_data_service import market_data_service
from analytics.financial_analysis_service import financial_analysis_service

logger = logging.getLogger(__name__)


class FundamentalsAgent:
    name = "fundamentals"

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] FundamentalsAgent starting analysis...")

        try:
            overview = await market_data_service.get_company_overview(self.ticker)
            income   = await market_data_service.get_income_statement(self.ticker)
            balance  = await market_data_service.get_balance_sheet(self.ticker)
            cashflow = await market_data_service.get_cash_flow(self.ticker)

            metrics = financial_analysis_service.compute(
                overview, income, balance, cashflow
            )

            system_prompt = (
                "You are a senior equity research analyst. Analyze a company's "
                "fundamentals and return a JSON object with this exact shape: "
                '{{"score": <float -1.0 to 1.0>, "confidence": <float 0.0 to 1.0>, '
                '"summary": "<2-3 sentences>", "evidence": ["bullet 1", "bullet 2", ...]}}'
            )

            mcap_str = f"${overview.market_cap/1e9:.1f}B" if overview.market_cap else "N/A"
            pe_str = f"{overview.pe_ratio:.2f}" if overview.pe_ratio else "N/A"
            fpe_str = f"{overview.forward_pe:.2f}" if overview.forward_pe else "N/A"
            nm_str = f"{metrics.net_margin:.1%}" if metrics.net_margin is not None else "N/A"
            roe_str = f"{metrics.return_on_equity:.1%}" if metrics.return_on_equity is not None else "N/A"
            revg_str = f"{metrics.revenue_growth:.1%}" if metrics.revenue_growth is not None else "N/A"
            earng_str = f"{metrics.earnings_growth:.1%}" if metrics.earnings_growth is not None else "N/A"
            fcf_str = f"${metrics.free_cash_flow/1e9:.1f}B" if metrics.free_cash_flow is not None else "N/A"

            user_prompt = f"""
Analyze the fundamentals of {overview.name} ({self.ticker}).

KEY METRICS:
- Sector: {overview.sector}
- Market cap: {mcap_str}
- P/E ratio: {pe_str}
- Forward P/E: {fpe_str}
- Net margin: {nm_str}
- Return on Equity: {roe_str}
- Revenue growth: {revg_str}
- Earnings growth: {earng_str}
- Free cash flow: {fcf_str}

PRE-COMPUTED SCORES:
- Financial health: {metrics.financial_health_score}
- Profitability: {metrics.profitability_score}
- Growth: {metrics.growth_score}
- Composite overall score: {metrics.overall_score}

KEY STRENGTHS: {metrics.key_strengths}
KEY RISKS: {metrics.key_risks}

Based on the data above, provide your final assessment as JSON.
Score should reflect overall bullish (positive) or bearish (negative) view.
Confidence should reflect how complete the data is.
Evidence bullets should cite specific numbers from above.
"""

            result = await call_llm(system_prompt, user_prompt)

            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", metrics.overall_score)),
                confidence=float(result.get("confidence", 0.7)),
                summary=result.get("summary", ""),
                evidence=result.get("evidence", metrics.key_strengths + metrics.key_risks),
            )

        except Exception as e:
            logger.error(f"[{self.ticker}] FundamentalsAgent failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Analysis failed: {e}", evidence=[]
            )

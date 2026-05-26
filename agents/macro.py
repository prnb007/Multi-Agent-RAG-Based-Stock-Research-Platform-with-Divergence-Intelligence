"""
MacroAgent
Uses SectorComparisonService for ALL sector/peer analysis.
NEVER calls yfinance or fetches prices directly.
"""

import logging
from agents.base import AgentOutput, call_llm
from providers.market_data_service import market_data_service
from analytics.sector_comparison_service import sector_comparison_service

logger = logging.getLogger(__name__)


class MacroAgent:
    name = "macro"

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] MacroAgent starting analysis...")

        try:
            overview = await market_data_service.get_company_overview(self.ticker)
            comparison = await sector_comparison_service.compare(
                self.ticker, overview.sector
            )

            system_prompt = (
                "You are a macro/sector analyst. Compare a stock's performance to its "
                "sector ETF and peers. Return a JSON object with this exact shape: "
                '{{"score": <float -1.0 to 1.0>, "confidence": <float 0.0 to 1.0>, '
                '"summary": "<2-3 sentences>", "evidence": ["bullet 1", "bullet 2", ...]}}'
            )

            user_prompt = f"""
Analyze {self.ticker}'s position vs its sector and peers.

SECTOR: {comparison.sector}
SECTOR ETF: {comparison.sector_etf}

3-MONTH RETURNS:
- {self.ticker}: {comparison.ticker_3mo_return}%
- {comparison.sector_etf} (sector ETF): {comparison.etf_3mo_return}%
- Outperformance vs ETF: {comparison.outperformance}%

PEER COMPARISON:
- Peers: {comparison.peer_tickers}
- Peer average return: {comparison.peer_avg_return}%
- Outperformance vs peers: {comparison.vs_peers}%

RELATIVE STRENGTH LABEL: {comparison.relative_strength}
PRE-COMPUTED MACRO SCORE: {comparison.macro_score}

Provide your final macro assessment as JSON.
Score: positive = outperforming sector/peers, negative = underperforming.
Evidence: cite specific percentage comparisons.
"""

            result = await call_llm(system_prompt, user_prompt)

            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", comparison.macro_score)),
                confidence=float(result.get("confidence", 0.7)),
                summary=result.get("summary", ""),
                evidence=result.get("evidence", []),
            )

        except Exception as e:
            logger.error(f"[{self.ticker}] MacroAgent failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Analysis failed: {e}", evidence=[]
            )

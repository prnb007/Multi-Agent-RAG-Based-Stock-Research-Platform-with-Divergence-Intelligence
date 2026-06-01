"""
MacroAgent
Uses SectorComparisonService for ALL sector/peer analysis.
NEVER calls yfinance or fetches prices directly.
Falls back to quote-based analysis if full price history is unavailable.
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

    async def _simple_macro_from_quote(self) -> AgentOutput:
        """
        Lightweight fallback when full price history is unavailable.
        Uses current quote (day change + 52w position) for a simple signal.
        """
        try:
            overview = await market_data_service.get_company_overview(self.ticker)
            quote    = await market_data_service.get_realtime_quote(self.ticker)

            pct = quote.percent_change
            # Score: +1.0 at +3% day gain, -1.0 at -3% day loss
            raw_score = round(max(-1.0, min(1.0, pct / 3.0)), 2)

            sector_note = f" Sector: {overview.sector}." if overview.sector else ""
            rev_growth  = (
                f" Revenue growth: {overview.revenue_growth:.1%}."
                if overview.revenue_growth is not None else ""
            )

            return AgentOutput(
                agent=self.name,
                score=raw_score,
                confidence=0.35,
                summary=(
                    f"{self.ticker} simplified macro view (full price history unavailable)."
                    f" Today: {pct:+.2f}%.{sector_note}{rev_growth}"
                ),
                evidence=[
                    f"Day change: {pct:+.2f}%",
                    f"Current price: ${quote.current_price:.2f}",
                    f"Day range: ${quote.day_low:.2f} – ${quote.day_high:.2f}",
                ] + (
                    [f"Revenue growth: {overview.revenue_growth:.1%}"]
                    if overview.revenue_growth is not None else []
                ),
            )
        except Exception as e:
            logger.error(f"[{self.ticker}] MacroAgent simple fallback failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Macro analysis temporarily unavailable for {self.ticker}. Provider rate-limited.",
                evidence=[]
            )

    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] MacroAgent starting analysis...")

        try:
            overview   = await market_data_service.get_company_overview(self.ticker)
            comparison = await sector_comparison_service.compare(
                self.ticker, overview.sector
            )

        except Exception as e:
            logger.warning(
                f"[{self.ticker}] MacroAgent full comparison failed ({e}), "
                "trying simplified quote-based fallback"
            )
            return await self._simple_macro_from_quote()

        try:
            # ── Pre-LLM fallback from sector comparison ──────────────────
            schema_fallback = {
                "score":      comparison.macro_score,
                "confidence": 0.6,
                "summary": (
                    f"{self.ticker} vs {comparison.sector_etf} sector ETF: "
                    f"{'outperforming' if (comparison.outperformance or 0) > 0 else 'underperforming'} "
                    f"by {abs(comparison.outperformance or 0):.1f}% over 3 months. "
                    f"Relative strength: {comparison.relative_strength}."
                ),
                "evidence": [
                    f"{self.ticker} 3-month return: {comparison.ticker_3mo_return}%",
                    f"{comparison.sector_etf} ETF return: {comparison.etf_3mo_return}%",
                    f"Outperformance vs ETF: {comparison.outperformance}%",
                    f"Peers: {comparison.peer_tickers}",
                    f"Peer average return: {comparison.peer_avg_return}%",
                ],
            }

            # ── Build prompts ────────────────────────────────────────────
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

            result = await call_llm(system_prompt, user_prompt, schema_fallback=schema_fallback)

            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", schema_fallback["score"])),
                confidence=float(result.get("confidence", schema_fallback["confidence"])),
                summary=result.get("summary") or schema_fallback["summary"],
                evidence=result.get("evidence") or schema_fallback["evidence"],
            )

        except Exception as e:
            logger.error(f"[{self.ticker}] MacroAgent LLM step failed: {e}")
            return AgentOutput(
                agent=self.name,
                score=comparison.macro_score,
                confidence=0.5,
                summary=schema_fallback["summary"],
                evidence=schema_fallback["evidence"],
            )

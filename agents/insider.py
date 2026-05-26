"""
InsiderAgent
Uses Finnhub (via MarketDataService) for clean insider transaction data.
No more SEC Form 4 XML parsing.
"""

import logging
from agents.base import AgentOutput, call_llm
from providers.market_data_service import market_data_service

logger = logging.getLogger(__name__)


class InsiderAgent:
    name = "insider"

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] InsiderAgent starting analysis...")

        try:
            trades = await market_data_service.get_insider_trades(
                self.ticker, limit=20
            )

            if not trades:
                return AgentOutput(
                    agent=self.name, score=0.0, confidence=0.4,
                    summary="No recent insider transactions found.",
                    evidence=[]
                )

            # Aggregate buy vs sell activity
            buys  = [t for t in trades if t.transaction_type == "buy"]
            sells = [t for t in trades if t.transaction_type == "sell"]
            total_buy_value  = sum(t.total_value or 0 for t in buys)
            total_sell_value = sum(t.total_value or 0 for t in sells)
            net_value        = total_buy_value - total_sell_value

            # Build evidence list for the prompt
            trade_lines = []
            for t in trades[:8]:
                value_str = (
                    f"${t.total_value/1e6:.2f}M"
                    if t.total_value and t.total_value >= 1e6
                    else f"${t.total_value:,.0f}"
                    if t.total_value else "value unknown"
                )
                trade_lines.append(
                    f"- {t.transaction_date}: {t.name} "
                    f"{t.transaction_type.upper()} {t.shares:,} shares "
                    f"({value_str})"
                )

            system_prompt = (
                "You are an insider trading analyst. Analyze insider transaction "
                "data and return a JSON object with this exact shape: "
                '{{"score": <float -1.0 to 1.0>, "confidence": <float 0.0 to 1.0>, '
                '"summary": "<2-3 sentences>", "evidence": ["bullet 1", "bullet 2", ...]}}'
            )

            user_prompt = f"""
Analyze insider activity for {self.ticker} based on recent Form 4 transactions.

AGGREGATE STATS (last 20 transactions):
- Total buy transactions: {len(buys)}
- Total sell transactions: {len(sells)}
- Total buy value: ${total_buy_value/1e6:.2f}M
- Total sell value: ${total_sell_value/1e6:.2f}M
- Net insider activity: ${net_value/1e6:.2f}M

RECENT TRANSACTIONS:
{chr(10).join(trade_lines)}

Provide your final assessment as JSON.
Score: positive = net insider buying (bullish), negative = net selling (bearish).
    Heavy selling alone is NOT always bearish — executives often sell for diversification/taxes.
    Heavy buying is generally a stronger bullish signal than selling is bearish.
Confidence: based on volume of insider activity and recency.
Evidence: cite specific transactions with names, amounts, and dates.
"""

            result = await call_llm(system_prompt, user_prompt)

            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", 0.0)),
                confidence=float(result.get("confidence", 0.6)),
                summary=result.get("summary", ""),
                evidence=result.get("evidence", [l[2:] for l in trade_lines[:5]]),
            )

        except Exception as e:
            logger.error(f"[{self.ticker}] InsiderAgent failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Analysis failed: {e}", evidence=[]
            )

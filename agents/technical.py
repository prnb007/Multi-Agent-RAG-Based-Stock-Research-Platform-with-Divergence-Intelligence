"""
TechnicalAgent
Uses TechnicalIndicatorService for ALL indicator calculations.
Uses MarketDataService for price history.
NEVER calls yfinance or computes indicators inline.
"""

import logging
from agents.base import AgentOutput, call_llm
from providers.market_data_service import market_data_service
from analytics.technical_indicator_service import technical_indicator_service

logger = logging.getLogger(__name__)


class TechnicalAgent:
    name = "technical"

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] TechnicalAgent starting analysis...")

        try:
            price_history = await market_data_service.get_price_history(self.ticker)
            signals = technical_indicator_service.compute(price_history)

            if signals.current_price is None:
                return AgentOutput(
                    agent=self.name, score=0.0, confidence=0.0,
                    summary="Insufficient price data for analysis",
                    evidence=[]
                )

            system_prompt = (
                "You are a technical analyst. Analyze technical indicators and return a JSON object "
                "with this exact shape: "
                '{{"score": <float -1.0 to 1.0>, "confidence": <float 0.0 to 1.0>, '
                '"summary": "<2-3 sentences>", "evidence": ["bullet 1", "bullet 2", ...]}}'
            )

            user_prompt = f"""
Analyze technical indicators for {self.ticker}.

PRICE: ${signals.current_price}
6-MONTH RETURN: {signals.six_month_return}%

MOMENTUM INDICATORS:
- RSI (14): {signals.rsi}
- MACD: {signals.macd}
- MACD signal: {signals.macd_signal}
- MACD histogram: {signals.macd_histogram}

MOVING AVERAGES:
- EMA 20: {signals.ema_20}
- EMA 50: {signals.ema_50}
- SMA 200: {signals.sma_200}

BOLLINGER BANDS:
- Upper: {signals.bb_upper}
- Middle: {signals.bb_middle}
- Lower: {signals.bb_lower}
- Price position: {signals.price_vs_bb}

VOLUME: {signals.volume_trend}
OVERALL TREND: {signals.trend}
PRE-COMPUTED MOMENTUM SCORE: {signals.momentum_score}

Provide your final technical assessment as JSON.
Score: positive = bullish technicals, negative = bearish technicals.
Confidence: how strong and consistent the signals are.
Evidence: cite specific numbers (RSI, MACD, position vs bands, etc.)
"""

            result = await call_llm(system_prompt, user_prompt)

            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", signals.momentum_score)),
                confidence=float(result.get("confidence", 0.7)),
                summary=result.get("summary", ""),
                evidence=result.get("evidence", []),
            )

        except Exception as e:
            logger.error(f"[{self.ticker}] TechnicalAgent failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Analysis failed: {e}", evidence=[]
            )

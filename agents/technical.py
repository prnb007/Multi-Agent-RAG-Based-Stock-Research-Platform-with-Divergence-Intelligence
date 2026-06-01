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

    @staticmethod
    def _build_evidence(signals) -> list[str]:
        ev = []
        if signals.rsi is not None:
            label = "overbought" if signals.rsi > 70 else "oversold" if signals.rsi < 30 else "neutral"
            ev.append(f"RSI(14): {signals.rsi:.1f} — {label}")
        if signals.macd is not None and signals.macd_signal is not None:
            cross = "bullish crossover" if signals.macd > signals.macd_signal else "bearish crossover"
            ev.append(f"MACD: {signals.macd:.3f} vs signal {signals.macd_signal:.3f} ({cross})")
        if signals.trend:
            ev.append(f"Trend: {signals.trend} (EMA20 vs EMA50)")
        if signals.price_vs_bb:
            ev.append(f"Price vs Bollinger Bands: {signals.price_vs_bb.replace('_', ' ')}")
        if signals.six_month_return is not None:
            ev.append(f"6-month return: {signals.six_month_return:+.2f}%")
        if signals.volume_trend:
            ev.append(f"Volume: {signals.volume_trend.replace('_', ' ')}")
        return ev or ["Insufficient price data for detailed technical evidence."]

    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] TechnicalAgent starting analysis...")

        try:
            price_history = await market_data_service.get_price_history(self.ticker)
            signals = technical_indicator_service.compute(price_history)

            if signals.current_price is None:
                return AgentOutput(
                    agent=self.name, score=0.0, confidence=0.0,
                    summary=f"Insufficient price data for {self.ticker} technical analysis.",
                    evidence=[]
                )

            # ── Pre-LLM fallback from indicator values ───────────────────
            trend_word = signals.trend or "neutral"
            rsi_note = ""
            if signals.rsi is not None:
                if signals.rsi > 70:
                    rsi_note = f" RSI at {signals.rsi:.0f} (overbought)."
                elif signals.rsi < 30:
                    rsi_note = f" RSI at {signals.rsi:.0f} (oversold)."
                else:
                    rsi_note = f" RSI at {signals.rsi:.0f}."

            return_note = (
                f" 6-month return: {signals.six_month_return:+.1f}%."
                if signals.six_month_return is not None else ""
            )

            schema_fallback = {
                "score":      float(signals.momentum_score),
                "confidence": 0.65,
                "summary": (
                    f"{self.ticker} technicals show a {trend_word} trend."
                    f"{rsi_note}{return_note}"
                    f" Price is {(signals.price_vs_bb or 'in band').replace('_', ' ')} vs Bollinger Bands."
                ),
                "evidence": self._build_evidence(signals),
            }

            # ── Build prompts ────────────────────────────────────────────
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

            result = await call_llm(system_prompt, user_prompt, schema_fallback=schema_fallback)

            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", schema_fallback["score"])),
                confidence=float(result.get("confidence", schema_fallback["confidence"])),
                summary=result.get("summary") or schema_fallback["summary"],
                evidence=result.get("evidence") or schema_fallback["evidence"],
            )

        except Exception as e:
            logger.error(f"[{self.ticker}] TechnicalAgent failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Price data temporarily unavailable for {self.ticker}. Provider may be rate-limited.",
                evidence=[]
            )

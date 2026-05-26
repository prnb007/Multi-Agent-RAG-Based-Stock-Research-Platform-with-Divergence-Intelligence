"""
TechnicalIndicatorService
Computes RSI, MACD, Bollinger Bands, EMA, SMA
from a normalized PriceHistory object.
Never calls any external API — pure computation only.
"""

import logging
import pandas as pd
import pandas_ta as ta
from dataclasses import dataclass
from typing import Optional
from providers.models import PriceHistory

logger = logging.getLogger(__name__)


@dataclass
class TechnicalSignals:
    ticker: str
    rsi: Optional[float]               # 0-100, >70 overbought, <30 oversold
    macd: Optional[float]              # MACD line value
    macd_signal: Optional[float]       # Signal line value
    macd_histogram: Optional[float]    # MACD - Signal
    bb_upper: Optional[float]          # Bollinger upper band
    bb_middle: Optional[float]         # Bollinger middle band (20-day SMA)
    bb_lower: Optional[float]          # Bollinger lower band
    ema_20: Optional[float]            # 20-day EMA
    ema_50: Optional[float]            # 50-day EMA
    sma_200: Optional[float]           # 200-day SMA
    current_price: Optional[float]     # Latest close price
    price_vs_bb: Optional[str]         # "above_upper" | "in_band" | "below_lower"
    trend: Optional[str]               # "bullish" | "bearish" | "neutral"
    momentum_score: float              # -1.0 to +1.0 composite score
    volume_trend: Optional[str]        # "above_average" | "below_average"
    six_month_return: Optional[float]  # % return over 6 months


class TechnicalIndicatorService:
    """
    Pure computation service — no API calls, no side effects.
    Input: normalized PriceHistory
    Output: TechnicalSignals dataclass
    """

    def compute(self, price_history: PriceHistory) -> TechnicalSignals:
        ticker = price_history.ticker

        if not price_history.points or len(price_history.points) < 20:
            logger.warning(f"[Technical] Insufficient price data for {ticker}")
            return TechnicalSignals(
                ticker=ticker, rsi=None, macd=None, macd_signal=None,
                macd_histogram=None, bb_upper=None, bb_middle=None,
                bb_lower=None, ema_20=None, ema_50=None, sma_200=None,
                current_price=None, price_vs_bb=None, trend=None,
                momentum_score=0.0, volume_trend=None, six_month_return=None
            )

        # Build DataFrame from normalized points (oldest first)
        points = sorted(price_history.points, key=lambda p: p.date)
        df = pd.DataFrame([{
            "close":  p.close,
            "high":   p.high,
            "low":    p.low,
            "open":   p.open,
            "volume": p.volume,
        } for p in points])

        # Compute indicators
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.sma(length=200, append=True)

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        def safe(col_pattern):
            cols = [c for c in df.columns if col_pattern.lower() in c.lower()]
            if cols:
                val = last[cols[0]]
                return float(val) if pd.notna(val) else None
            return None

        rsi          = safe("RSI_14")
        macd         = safe("MACD_12_26_9")
        macd_signal  = safe("MACDs_12_26_9")
        macd_hist    = safe("MACDh_12_26_9")
        bb_upper     = safe("BBU_20_2.0")
        bb_middle    = safe("BBM_20_2.0")
        bb_lower     = safe("BBL_20_2.0")
        ema_20       = safe("EMA_20")
        ema_50       = safe("EMA_50")
        sma_200      = safe("SMA_200")
        current      = float(last["close"])

        # Price vs Bollinger Bands
        price_vs_bb = None
        if bb_upper and bb_lower:
            if current > bb_upper:
                price_vs_bb = "above_upper"
            elif current < bb_lower:
                price_vs_bb = "below_lower"
            else:
                price_vs_bb = "in_band"

        # Trend: bullish if EMA20 > EMA50 and price above both
        trend = "neutral"
        if ema_20 and ema_50:
            if ema_20 > ema_50 and current > ema_20:
                trend = "bullish"
            elif ema_20 < ema_50 and current < ema_20:
                trend = "bearish"

        # Volume trend
        avg_volume = df["volume"].tail(14).mean()
        volume_trend = (
            "above_average" if float(last["volume"]) > avg_volume
            else "below_average"
        )

        # 6-month return
        six_month_return = None
        if len(points) >= 2:
            oldest_close = points[0].close
            if oldest_close > 0:
                six_month_return = round(
                    (current - oldest_close) / oldest_close * 100, 2
                )

        # Momentum score: composite -1.0 to +1.0
        scores = []
        if rsi:
            scores.append((rsi - 50) / 50)
        if macd and macd_signal:
            scores.append(0.3 if macd > macd_signal else -0.3)
        if trend == "bullish":
            scores.append(0.4)
        elif trend == "bearish":
            scores.append(-0.4)
        if price_vs_bb == "above_upper":
            scores.append(-0.2)
        elif price_vs_bb == "below_lower":
            scores.append(0.2)

        momentum_score = round(
            max(-1.0, min(1.0, sum(scores) / len(scores))) if scores else 0.0,
            3
        )

        return TechnicalSignals(
            ticker=ticker,
            rsi=round(rsi, 2) if rsi else None,
            macd=round(macd, 4) if macd else None,
            macd_signal=round(macd_signal, 4) if macd_signal else None,
            macd_histogram=round(macd_hist, 4) if macd_hist else None,
            bb_upper=round(bb_upper, 2) if bb_upper else None,
            bb_middle=round(bb_middle, 2) if bb_middle else None,
            bb_lower=round(bb_lower, 2) if bb_lower else None,
            ema_20=round(ema_20, 2) if ema_20 else None,
            ema_50=round(ema_50, 2) if ema_50 else None,
            sma_200=round(sma_200, 2) if sma_200 else None,
            current_price=round(current, 2),
            price_vs_bb=price_vs_bb,
            trend=trend,
            momentum_score=momentum_score,
            volume_trend=volume_trend,
            six_month_return=six_month_return,
        )


technical_indicator_service = TechnicalIndicatorService()

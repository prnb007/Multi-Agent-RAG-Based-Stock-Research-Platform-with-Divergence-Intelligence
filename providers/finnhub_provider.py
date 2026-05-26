"""
FinnhubProvider — Primary provider for:
  - OHLCV daily candles
  - Company news + sentiment scores
  - Insider transactions
  - Peer tickers
  - Real-time quotes (BONUS feature)
  - Analyst recommendations

Returns normalized models from providers/models.py.
Uses httpx.AsyncClient for async calls.
"""

import os
import logging
import time
import httpx
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from providers.models import (
    CompanyOverview, PriceHistory, PricePoint,
    NewsItem, InsiderTransaction, AnalystRecommendation,
    RealtimeQuote, SentimentSummary
)
from providers.retry_service import standard_retry, aggressive_retry, light_retry

load_dotenv()
logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"
FINNHUB_KEY  = os.getenv("FINNHUB_API_KEY", "")


class FinnhubProvider:
    """
    Finnhub data provider. Free tier supports 60 requests/minute.
    All methods return normalized Pydantic models.
    """

    def __init__(self):
        self.name = "finnhub"
        self._client = httpx.AsyncClient(timeout=15.0)

    async def _get(self, endpoint: str, params: dict) -> dict:
        params["token"] = FINNHUB_KEY
        url = f"{FINNHUB_BASE}{endpoint}"
        response = await self._client.get(url, params=params)
        if response.status_code == 429:
            raise httpx.HTTPStatusError(
                "Finnhub rate limit hit",
                request=response.request,
                response=response
            )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # OHLCV: stock candles
    # ------------------------------------------------------------------
    @aggressive_retry
    async def get_price_history(self, ticker: str) -> PriceHistory:
        """6-month daily OHLCV history."""
        logger.info(f"[Finnhub] Fetching price history for {ticker}")
        to_ts   = int(time.time())
        from_ts = to_ts - (180 * 24 * 60 * 60)   # 180 days back

        data = await self._get("/stock/candle", {
            "symbol":     ticker,
            "resolution": "D",
            "from":       from_ts,
            "to":         to_ts,
        })

        if data.get("s") != "ok" or not data.get("t"):
            raise ValueError(f"Finnhub returned empty candles for {ticker}")

        points = []
        for i in range(len(data["t"])):
            try:
                points.append(PricePoint(
                    date=datetime.utcfromtimestamp(data["t"][i]).strftime("%Y-%m-%d"),
                    open=float(data["o"][i]),
                    high=float(data["h"][i]),
                    low=float(data["l"][i]),
                    close=float(data["c"][i]),
                    volume=int(data["v"][i]),
                ))
            except (KeyError, IndexError, ValueError):
                continue

        if not points:
            raise ValueError(f"Failed to parse any candles for {ticker}")

        return PriceHistory(
            ticker=ticker.upper(),
            interval="daily",
            points=sorted(points, key=lambda p: p.date, reverse=True),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    # ------------------------------------------------------------------
    # Company profile — used as backup overview source
    # ------------------------------------------------------------------
    @standard_retry
    async def get_company_overview(self, ticker: str) -> CompanyOverview:
        """Basic profile via /stock/profile2 + current price via /quote."""
        logger.info(f"[Finnhub] Fetching profile for {ticker}")

        profile = await self._get("/stock/profile2", {"symbol": ticker})
        if not profile or "name" not in profile:
            raise ValueError(f"Finnhub returned empty profile for {ticker}")

        # Fetch current price separately
        try:
            quote = await self._get("/quote", {"symbol": ticker})
            current_price = float(quote.get("c", 0)) or None
        except Exception:
            current_price = None

        return CompanyOverview(
            ticker=ticker.upper(),
            name=profile.get("name", ticker),
            sector=(profile.get("finnhubIndustry") or "Unknown").upper(),
            industry=profile.get("finnhubIndustry", "Unknown"),
            description=None,
            market_cap=(
                float(profile.get("marketCapitalization", 0)) * 1_000_000
                if profile.get("marketCapitalization") else None
            ),
            pe_ratio=None,
            forward_pe=None,
            price_to_book=None,
            debt_to_equity=None,
            return_on_equity=None,
            revenue_growth=None,
            earnings_growth=None,
            current_price=current_price,
            fifty_two_week_high=None,
            fifty_two_week_low=None,
            dividend_yield=None,
            beta=None,
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    # ------------------------------------------------------------------
    # Real-time quote — BONUS feature
    # ------------------------------------------------------------------
    @light_retry
    async def get_realtime_quote(self, ticker: str) -> RealtimeQuote:
        """Live price snapshot. Use this for the Screener UI."""
        logger.info(f"[Finnhub] Fetching realtime quote for {ticker}")
        q = await self._get("/quote", {"symbol": ticker})

        if not q or "c" not in q or q["c"] == 0:
            raise ValueError(f"Finnhub returned empty quote for {ticker}")

        return RealtimeQuote(
            ticker=ticker.upper(),
            current_price=float(q["c"]),
            change=float(q.get("d", 0)),
            percent_change=float(q.get("dp", 0)),
            day_high=float(q.get("h", 0)),
            day_low=float(q.get("l", 0)),
            day_open=float(q.get("o", 0)),
            prev_close=float(q.get("pc", 0)),
            timestamp=int(q.get("t", 0)),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    # ------------------------------------------------------------------
    # News headlines + sentiment
    # ------------------------------------------------------------------
    @standard_retry
    async def get_news(self, ticker: str, limit: int = 20) -> list[NewsItem]:
        """Company news from the last 30 days with sentiment when available."""
        logger.info(f"[Finnhub] Fetching news for {ticker}")
        to_date   = datetime.utcnow().strftime("%Y-%m-%d")
        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

        articles = await self._get("/company-news", {
            "symbol": ticker,
            "from":   from_date,
            "to":     to_date,
        })

        if not isinstance(articles, list):
            return []

        items = []
        for a in articles[:limit]:
            try:
                items.append(NewsItem(
                    title=a.get("headline", ""),
                    summary=a.get("summary"),
                    url=a.get("url", ""),
                    source=a.get("source", "Finnhub"),
                    published_at=datetime.utcfromtimestamp(
                        a.get("datetime", 0)
                    ).isoformat(),
                    sentiment_score=None,  # Aggregated sentiment fetched separately
                    provider=self.name,
                    fetched_at=datetime.utcnow()
                ))
            except Exception:
                continue
        return items

    # ------------------------------------------------------------------
    # Aggregated sentiment summary
    # ------------------------------------------------------------------
    @light_retry
    async def get_sentiment_summary(self, ticker: str) -> Optional[SentimentSummary]:
        """Finnhub's aggregated news sentiment score."""
        logger.info(f"[Finnhub] Fetching sentiment for {ticker}")
        try:
            data = await self._get("/news-sentiment", {"symbol": ticker})
            if not data or "companyNewsScore" not in data:
                return None
            return SentimentSummary(
                ticker=ticker.upper(),
                buzz_articles_in_last_week=int(
                    data.get("buzz", {}).get("articlesInLastWeek", 0)
                ),
                news_score=float(data.get("companyNewsScore", 0)),
                sector_average_buzz=data.get("sectorAverageBullishPercent"),
                sector_average_news_score=data.get("sectorAverageNewsScore"),
                provider=self.name,
                fetched_at=datetime.utcnow()
            )
        except Exception as e:
            logger.warning(f"[Finnhub] sentiment fetch failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Insider transactions
    # ------------------------------------------------------------------
    @standard_retry
    async def get_insider_trades(
        self, ticker: str, limit: int = 20
    ) -> list[InsiderTransaction]:
        """Recent Form 4 insider transactions via Finnhub."""
        logger.info(f"[Finnhub] Fetching insider trades for {ticker}")
        data = await self._get("/stock/insider-transactions", {"symbol": ticker})

        trades = data.get("data", []) if isinstance(data, dict) else []
        items = []

        for t in trades[:limit]:
            try:
                shares = int(t.get("change", 0))
                if shares == 0:
                    continue

                if "transactionCode" in t:
                    code = t["transactionCode"]
                    tx_type = (
                        "buy"   if code in ("P", "A") else
                        "sell"  if code in ("S", "D") else
                        "option_exercise" if code == "M" else
                        "other"
                    )
                else:
                    tx_type = "buy" if shares > 0 else "sell"

                share_price = float(t.get("transactionPrice", 0)) or None
                total_value = (
                    abs(shares) * share_price
                    if share_price else None
                )

                items.append(InsiderTransaction(
                    ticker=ticker.upper(),
                    name=t.get("name", "Unknown"),
                    transaction_date=t.get("transactionDate", ""),
                    transaction_type=tx_type,
                    shares=abs(shares),
                    share_price=share_price,
                    total_value=total_value,
                    position=t.get("position"),
                    provider=self.name,
                    fetched_at=datetime.utcnow()
                ))
            except Exception as e:
                logger.debug(f"[Finnhub] skipping malformed trade: {e}")
                continue

        return items

    # ------------------------------------------------------------------
    # Peer tickers
    # ------------------------------------------------------------------
    @light_retry
    async def get_peers(self, ticker: str) -> list[str]:
        """Return list of peer ticker symbols. Used by MacroAgent."""
        logger.info(f"[Finnhub] Fetching peers for {ticker}")
        data = await self._get("/stock/peers", {"symbol": ticker})
        if not isinstance(data, list):
            return []
        return [
            p for p in data
            if isinstance(p, str) and p.upper() != ticker.upper()
        ][:10]

    # ------------------------------------------------------------------
    # Analyst recommendations
    # ------------------------------------------------------------------
    @standard_retry
    async def get_recommendations(
        self, ticker: str
    ) -> Optional[AnalystRecommendation]:
        """Most recent analyst consensus."""
        logger.info(f"[Finnhub] Fetching recommendations for {ticker}")
        data = await self._get("/stock/recommendation", {"symbol": ticker})
        if not isinstance(data, list) or not data:
            return None

        latest = data[0]
        strong_buy  = int(latest.get("strongBuy", 0))
        buy         = int(latest.get("buy", 0))
        hold        = int(latest.get("hold", 0))
        sell        = int(latest.get("sell", 0))
        strong_sell = int(latest.get("strongSell", 0))
        total = strong_buy + buy + hold + sell + strong_sell
        if total == 0:
            return None

        # Compute consensus score: -1.0 (strong sell) to +1.0 (strong buy)
        consensus_score = (
            (strong_buy * 1.0 + buy * 0.5 + hold * 0 - sell * 0.5 - strong_sell * 1.0)
            / total
        )

        return AnalystRecommendation(
            ticker=ticker.upper(),
            period=latest.get("period", ""),
            strong_buy=strong_buy,
            buy=buy,
            hold=hold,
            sell=sell,
            strong_sell=strong_sell,
            total=total,
            consensus_score=round(consensus_score, 3),
            provider=self.name,
            fetched_at=datetime.utcnow()
        )

    async def close(self):
        await self._client.aclose()

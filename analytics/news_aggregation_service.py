"""
NewsAggregationService
Centralized news fetching from all sources.
Unified interface: get_company_news(ticker)
"""

import os
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Optional
from providers.models import NewsItem
from providers.market_data_service import market_data_service

logger = logging.getLogger(__name__)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


class NewsAggregationService:

    async def get_company_news(
        self, ticker: str, company_name: str = "", limit: int = 20
    ) -> list[NewsItem]:
        """
        Fetch news from all available sources.
        Deduplicates by title. Returns merged, sorted list.
        """
        results = await asyncio.gather(
            self._from_alpha_vantage(ticker, limit),
            self._from_newsapi(company_name or ticker, limit),
            return_exceptions=True
        )

        all_items = []
        for r in results:
            if isinstance(r, list):
                all_items.extend(r)

        # Deduplicate by title
        seen, unique = set(), []
        for item in all_items:
            key = item.title.lower()[:60]
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return sorted(
            unique,
            key=lambda x: x.published_at,
            reverse=True
        )[:limit]

    async def _from_alpha_vantage(
        self, ticker: str, limit: int
    ) -> list[NewsItem]:
        try:
            return await market_data_service.get_news(ticker, limit)
        except Exception as e:
            logger.warning(f"[News] AV news failed for {ticker}: {e}")
            return []

    async def _from_newsapi(
        self, query: str, limit: int
    ) -> list[NewsItem]:
        if not NEWS_API_KEY:
            return []
        try:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": query,
                    "from": from_date,
                    "language": "en",
                    "sortBy": "relevancy",
                    "pageSize": limit,
                    "apiKey": NEWS_API_KEY,
                },
                timeout=10
            ))
            articles = resp.json().get("articles", [])
            return [
                NewsItem(
                    title=a.get("title", ""),
                    summary=a.get("description"),
                    url=a.get("url", ""),
                    source=a.get("source", {}).get("name", "NewsAPI"),
                    published_at=a.get("publishedAt", ""),
                    sentiment_score=None,
                    provider="newsapi",
                    fetched_at=datetime.utcnow()
                )
                for a in articles
                if a.get("title") and "[Removed]" not in a.get("title", "")
            ]
        except Exception as e:
            logger.warning(f"[News] NewsAPI failed for {query}: {e}")
            return []

    def compute_sentiment_summary(
        self, news_items: list[NewsItem]
    ) -> dict:
        """
        Compute overall sentiment from news items that have scores.
        Returns summary dict for agent use.
        """
        scored = [
            n for n in news_items
            if n.sentiment_score is not None
        ]
        if not scored:
            return {
                "avg_sentiment": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": len(news_items),
                "sentiment_label": "neutral",
            }

        scores = [n.sentiment_score for n in scored]
        avg = sum(scores) / len(scores)
        positive = sum(1 for s in scores if s > 0.1)
        negative = sum(1 for s in scores if s < -0.1)
        neutral  = len(scores) - positive - negative

        label = (
            "positive" if avg > 0.1
            else "negative" if avg < -0.1
            else "neutral"
        )

        return {
            "avg_sentiment": round(avg, 4),
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "sentiment_label": label,
        }


news_aggregation_service = NewsAggregationService()

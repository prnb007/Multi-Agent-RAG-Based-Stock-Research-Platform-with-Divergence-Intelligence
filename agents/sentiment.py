"""
SentimentAgent
Uses NewsAggregationService for all news fetching and sentiment.
NEVER calls yfinance or NewsAPI directly.
"""

import logging
from agents.base import AgentOutput, call_llm
from providers.market_data_service import market_data_service
from analytics.news_aggregation_service import news_aggregation_service

logger = logging.getLogger(__name__)


class SentimentAgent:
    name = "sentiment"

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()

    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] SentimentAgent starting analysis...")

        try:
            overview = await market_data_service.get_company_overview(self.ticker)
            news = await news_aggregation_service.get_company_news(
                self.ticker, overview.name
            )
            sentiment = news_aggregation_service.compute_sentiment_summary(news)

            if not news:
                return AgentOutput(
                    agent=self.name, score=0.0, confidence=0.2,
                    summary=f"No recent news found for {self.ticker}. Sentiment cannot be assessed.",
                    evidence=[]
                )

            headlines = [f"- {item.title}" for item in news[:8]]

            # ── Pre-LLM fallback from sentiment aggregation ──────────────
            raw_score = float(sentiment["avg_sentiment"])
            schema_fallback = {
                "score":      round(max(-1.0, min(1.0, raw_score)), 2),
                "confidence": min(0.8, 0.3 + len(news) / 20),
                "summary": (
                    f"{overview.name} ({self.ticker}) — {len(news)} recent articles. "
                    f"Sentiment: {sentiment['sentiment_label']} "
                    f"({sentiment['positive_count']} positive, "
                    f"{sentiment['negative_count']} negative, "
                    f"{sentiment['neutral_count']} neutral)."
                ),
                "evidence": [h[2:] for h in headlines[:5]],
            }

            # ── Build prompts ────────────────────────────────────────────
            system_prompt = (
                "You are a financial news analyst. Analyze sentiment from recent news "
                "headlines and return a JSON object with this exact shape: "
                '{{"score": <float -1.0 to 1.0>, "confidence": <float 0.0 to 1.0>, '
                '"summary": "<2-3 sentences>", "evidence": ["headline 1", "headline 2", ...]}}'
            )

            user_prompt = f"""
Analyze sentiment for {overview.name} ({self.ticker}) based on recent news.

AGGREGATED SENTIMENT (pre-computed):
- Average sentiment score: {sentiment['avg_sentiment']}
- Positive headlines: {sentiment['positive_count']}
- Negative headlines: {sentiment['negative_count']}
- Neutral headlines: {sentiment['neutral_count']}
- Overall label: {sentiment['sentiment_label']}

RECENT HEADLINES:
{chr(10).join(headlines)}

Provide your final sentiment assessment as JSON.
Score should be between -1.0 (very bearish news) and +1.0 (very bullish news).
Confidence should reflect how recent and varied the news coverage is.
Evidence should cite specific headlines (4-5 most relevant).
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
            logger.error(f"[{self.ticker}] SentimentAgent failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Sentiment analysis temporarily unavailable for {self.ticker}. News provider may be rate-limited.",
                evidence=[]
            )

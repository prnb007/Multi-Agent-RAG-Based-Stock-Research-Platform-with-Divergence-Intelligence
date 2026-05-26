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
                    agent=self.name, score=0.0, confidence=0.0,
                    summary="No recent news available",
                    evidence=[]
                )

            # Pick top 8 most relevant headlines for the prompt
            headlines = [
                f"- {item.title}" for item in news[:8]
            ]

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

            result = await call_llm(system_prompt, user_prompt)

            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", sentiment["avg_sentiment"])),
                confidence=float(result.get("confidence", 0.7)),
                summary=result.get("summary", ""),
                evidence=result.get("evidence", [h[2:] for h in headlines[:5]]),
            )

        except Exception as e:
            logger.error(f"[{self.ticker}] SentimentAgent failed: {e}")
            return AgentOutput(
                agent=self.name, score=0.0, confidence=0.0,
                summary=f"Analysis failed: {e}", evidence=[]
            )

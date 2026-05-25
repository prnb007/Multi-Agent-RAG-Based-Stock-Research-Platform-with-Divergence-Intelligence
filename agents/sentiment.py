import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent, AgentOutput
from fetchers import fetch_news, fetch_stock_info

logger = logging.getLogger(__name__)

class SentimentAgent(BaseAgent):
    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] SentimentAgent starting analysis...")
        try:
            info = fetch_stock_info(self.ticker)
            news_articles = fetch_news(self.ticker, info.name, days_back=30)
            
            if not news_articles:
                return AgentOutput(
                    score=0.0,
                    confidence=0.1,
                    summary="No recent news found to analyze sentiment.",
                    evidence=[]
                )
            
            # Prepare news context (limit to top 15 articles to save tokens)
            news_context = ""
            for i, article in enumerate(news_articles[:15]):
                news_context += f"Title: {article.title}\nDate: {article.published_at}\nSnippet: {article.description}\n---\n"
            
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            structured_llm = llm.with_structured_output(AgentOutput)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert sentiment analysis AI agent. Your job is to analyze news articles and potential earnings transcripts snippets to gauge the market sentiment for a stock. Detect tone shifts, management sentiment, and public perception. Return a score from -1.0 (very negative sentiment) to +1.0 (very positive sentiment), a confidence score, a short summary, and a list of evidence bullet points."),
                ("user", "Analyze the sentiment for {ticker} ({company}).\n\nRecent News:\n{news_context}")
            ])
            
            chain = prompt | structured_llm
            result = await chain.ainvoke({
                "ticker": self.ticker,
                "company": info.name,
                "news_context": news_context
            })
            
            return result
        except Exception as e:
            logger.error(f"[{self.ticker}] SentimentAgent failed: {e}")
            return AgentOutput(
                score=0.0,
                confidence=0.0,
                summary=f"Analysis failed: {str(e)}",
                evidence=[]
            )

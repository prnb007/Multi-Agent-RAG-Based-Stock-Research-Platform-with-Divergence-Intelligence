import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent, AgentOutput
from fetchers import parse_insider_trades, fetch_sec_filings

logger = logging.getLogger(__name__)

class InsiderAgent(BaseAgent):
    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] InsiderAgent starting analysis...")
        try:
            # fetch_sec_filings is already downloading Form 4s (limit 20)
            # So parse_insider_trades will use them
            fetch_sec_filings(self.ticker)
            trades = parse_insider_trades(self.ticker)
            
            if not trades:
                return AgentOutput(
                    score=0.0,
                    confidence=0.5,
                    summary="No recent insider trades found (Form 4).",
                    evidence=[]
                )
                
            trades_context = ""
            for t in trades[:30]:
                trades_context += f"Filer: {t.filer_name}, Type: {t.transaction_type}, Shares: {t.shares}, Price: {t.price_per_share}, Date: {t.date}\n"
            
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            structured_llm = llm.with_structured_output(AgentOutput)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert insider trading analyst. Your job is to evaluate SEC Form 4 filings to determine if corporate insiders are buying or selling. Consider the buy/sell ratio, trade sizes, and recency. Return a score from -1.0 (bearish, heavy selling) to +1.0 (bullish, heavy buying), a confidence score, a short summary, and evidence bullet points."),
                ("user", "Analyze the recent insider trades for {ticker}:\n\n{trades_context}")
            ])
            
            chain = prompt | structured_llm
            result = await chain.ainvoke({
                "ticker": self.ticker,
                "trades_context": trades_context
            })
            
            return result
        except Exception as e:
            logger.error(f"[{self.ticker}] InsiderAgent failed: {e}")
            return AgentOutput(
                score=0.0,
                confidence=0.0,
                summary=f"Analysis failed: {str(e)}",
                evidence=[]
            )

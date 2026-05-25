import logging
import yfinance as yf
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent, AgentOutput
from fetchers import fetch_peers, fetch_sector_etf_performance

logger = logging.getLogger(__name__)

class MacroAgent(BaseAgent):
    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] MacroAgent starting analysis...")
        try:
            # Sector ETF performance (contains ticker return too)
            etf_perf = fetch_sector_etf_performance(self.ticker)
            
            # Peer performance
            peers = fetch_peers(self.ticker)
            peer_perf = {}
            for peer in peers:
                try:
                    hist = yf.download(peer, period="3mo", progress=False)["Close"]
                    if not hist.empty:
                        ret = float((hist.iloc[-1] - hist.iloc[0]) / hist.iloc[0] * 100)
                        peer_perf[peer] = round(ret, 2)
                except Exception:
                    pass
            
            macro_data = {
                "sector_etf_comparison": etf_perf,
                "peer_3mo_returns": peer_perf
            }
            
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            structured_llm = llm.with_structured_output(AgentOutput)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert macroeconomic and relative value analyst. Your job is to compare a stock's recent performance against its sector ETF and top peers. Evaluate if it's outperforming or underperforming the broader sector and its competitors. Return a score from -1.0 (severe underperformance) to +1.0 (strong outperformance), a confidence score, a short summary, and evidence bullet points."),
                ("user", "Analyze the relative performance for {ticker}:\n\n{macro_data}")
            ])
            
            chain = prompt | structured_llm
            result = await chain.ainvoke({
                "ticker": self.ticker,
                "macro_data": str(macro_data)
            })
            
            return result
        except Exception as e:
            logger.error(f"[{self.ticker}] MacroAgent failed: {e}")
            return AgentOutput(
                score=0.0,
                confidence=0.0,
                summary=f"Analysis failed: {str(e)}",
                evidence=[]
            )

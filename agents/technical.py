import logging
import pandas_ta as ta
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from agents.base import BaseAgent, AgentOutput
from fetchers import fetch_price_history

logger = logging.getLogger(__name__)

class TechnicalAgent(BaseAgent):
    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] TechnicalAgent starting analysis...")
        try:
            # Fetch 6mo history
            df = fetch_price_history(self.ticker, period="6mo")
            
            if df.empty or len(df) < 50:
                return AgentOutput(
                    score=0.0,
                    confidence=0.1,
                    summary="Not enough price history for technical analysis.",
                    evidence=[]
                )
            
            # Calculate technical indicators using pandas-ta
            df.ta.rsi(length=14, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.bbands(length=20, std=2, append=True)
            
            # Get the most recent row
            latest = df.iloc[-1]
            
            rsi_key = [c for c in df.columns if 'RSI' in c][0]
            macd_key = [c for c in df.columns if 'MACD' in c and 'MACDh' not in c and 'MACDs' not in c][0]
            macds_key = [c for c in df.columns if 'MACDs' in c][0]
            bbl_key = [c for c in df.columns if 'BBL' in c][0]
            bbu_key = [c for c in df.columns if 'BBU' in c][0]
            bbm_key = [c for c in df.columns if 'BBM' in c][0]
            
            tech_data = {
                "latest_close": latest["Close"],
                "rsi_14": latest[rsi_key],
                "macd": latest[macd_key],
                "macd_signal": latest[macds_key],
                "bb_lower": latest[bbl_key],
                "bb_upper": latest[bbu_key],
                "bb_middle": latest[bbm_key],
                "volume": latest["Volume"],
                "avg_volume_14": df["Volume"].rolling(14).mean().iloc[-1]
            }
            
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
            structured_llm = llm.with_structured_output(AgentOutput)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert technical analysis AI agent. Analyze the provided technical indicators (RSI, MACD, Bollinger Bands, Volume) to determine the short-to-medium term momentum and trend. Return a score from -1.0 (bearish, overbought, downtrend) to +1.0 (bullish, oversold, uptrend), a confidence score, a short summary, and evidence bullet points."),
                ("user", "Analyze the technical indicators for {ticker}:\n\n{tech_data}")
            ])
            
            chain = prompt | structured_llm
            result = await chain.ainvoke({
                "ticker": self.ticker,
                "tech_data": str(tech_data)
            })
            
            return result
        except Exception as e:
            logger.error(f"[{self.ticker}] TechnicalAgent failed: {e}")
            return AgentOutput(
                score=0.0,
                confidence=0.0,
                summary=f"Analysis failed: {str(e)}",
                evidence=[]
            )

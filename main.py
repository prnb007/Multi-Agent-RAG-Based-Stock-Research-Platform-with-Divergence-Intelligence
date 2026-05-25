"""
main.py
FastAPI application entry point.
Day 1: health check + /data/{ticker} to test all fetchers.
Later days will add /analyze/{ticker} with SSE streaming.
"""

import logging
import os
import json
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from fetchers import (
    fetch_stock_info,
    fetch_price_history,
    fetch_financials,
    fetch_news,
    fetch_sec_filings,
    parse_insider_trades,
    fetch_peers,
    fetch_sector_etf_performance,
)

from agents.fundamentals import FundamentalsAgent
from agents.sentiment import SentimentAgent
from agents.insider import InsiderAgent
from agents.technical import TechnicalAgent
from agents.macro import MacroAgent
from agents.synthesis import SynthesisAgent
from agents.base import AgentOutput

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StockLens API",
    description="Multi-agent stock research with divergence intelligence",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ── Day 1 test endpoint ───────────────────────────────────────────

@app.get("/data/{ticker}")
async def get_raw_data(ticker: str):
    """
    Test endpoint — verifies all data sources are working.
    Returns raw data from yfinance, SEC, and NewsAPI.
    This endpoint will be removed once agents are live.
    """
    ticker = ticker.upper().strip()
    logger.info(f"Fetching raw data for {ticker}")

    try:
        # 1. Stock info + fundamentals
        info = fetch_stock_info(ticker)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticker not found: {e}")

    # 2. Price history (last 6 months, condensed)
    try:
        history = fetch_price_history(ticker, period="6mo")
        price_summary = {
            "latest_close": round(float(history["Close"].iloc[-1]), 2),
            "6mo_high": round(float(history["High"].max()), 2),
            "6mo_low": round(float(history["Low"].min()), 2),
            "avg_volume": int(history["Volume"].mean()),
            "data_points": len(history),
        }
    except Exception as e:
        logger.warning(f"Price history failed: {e}")
        price_summary = {}

    # 3. News articles
    news = fetch_news(ticker, info.name)

    # 4. SEC filings (download, then list what we got)
    try:
        sec_paths = fetch_sec_filings(ticker)
        sec_summary = {
            "10-K_count": len(sec_paths.get("10-K", [])),
            "10-Q_count": len(sec_paths.get("10-Q", [])),
            "form4_count": len(sec_paths.get("4", [])),
        }
    except Exception as e:
        logger.warning(f"SEC fetch failed: {e}")
        sec_summary = {"error": str(e)}

    # 5. Insider trades
    try:
        trades = parse_insider_trades(ticker)
        insider_summary = {
            "total_trades": len(trades),
            "buys": sum(1 for t in trades if t.transaction_type == "Buy"),
            "sells": sum(1 for t in trades if t.transaction_type == "Sell"),
            "recent_trades": [t.model_dump() for t in trades[:5]],
        }
    except Exception as e:
        logger.warning(f"Insider parse failed: {e}")
        insider_summary = {}

    # 6. Sector + peer performance
    peers = fetch_peers(ticker)
    macro = fetch_sector_etf_performance(ticker)

    return {
        "ticker": ticker,
        "fetched_at": datetime.utcnow().isoformat(),
        "company": info.model_dump(),
        "price_summary": price_summary,
        "news": {
            "count": len(news),
            "articles": [a.model_dump() for a in news[:5]],  # preview first 5
        },
        "sec_filings": sec_summary,
        "insider_trades": insider_summary,
        "peers": peers,
        "macro": macro,
    }


# ── Agent Orchestration Endpoint ─────────────────────────────────

@app.get("/analyze/{ticker}")
async def analyze_ticker(ticker: str):
    ticker = ticker.upper().strip()
    
    async def event_generator():
        # Initialize agents
        agents = {
            "fundamentals": FundamentalsAgent(ticker),
            "sentiment": SentimentAgent(ticker),
            "insider": InsiderAgent(ticker),
            "technical": TechnicalAgent(ticker),
            "macro": MacroAgent(ticker),
        }
        
        results = {}
        
        # Wrapper to handle agent exceptions cleanly
        async def run_agent(name: str, agent):
            try:
                result = await agent.analyze()
                return name, result
            except Exception as e:
                logger.error(f"Error in agent task {name}: {e}")
                return name, AgentOutput(
                    score=0.0,
                    confidence=0.0,
                    summary=f"Agent failed: {str(e)}",
                    evidence=[]
                )

        # Create tasks for all agents
        tasks = [asyncio.create_task(run_agent(name, agent)) for name, agent in agents.items()]
        
        # Stream results as they complete
        for coro in asyncio.as_completed(tasks):
            name, result = await coro
            
            results[name] = result
            
            # Yield the SSE event
            data = {
                "agent": name,
                "score": result.score,
                "confidence": result.confidence,
                "summary": result.summary,
                "evidence": result.evidence
            }
            yield f"event: agent_complete\ndata: {json.dumps(data)}\n\n"
                
        # Now run the synthesis agent
        try:
            synthesis_agent = SynthesisAgent(ticker)
            synthesis_result = await synthesis_agent.analyze(results)
            
            synthesis_data = {
                "divergence_score": synthesis_result.divergence_score,
                "highest_gap_pair": synthesis_result.highest_gap_pair,
                "bull_thesis": synthesis_result.bull_thesis,
                "bear_thesis": synthesis_result.bear_thesis
            }
            yield f"event: report_complete\ndata: {json.dumps(synthesis_data)}\n\n"
        except Exception as e:
            logger.error(f"Error in synthesis agent: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

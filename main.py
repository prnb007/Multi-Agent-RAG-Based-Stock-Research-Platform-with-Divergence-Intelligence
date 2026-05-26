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
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "*",  # temporary — tighten after deployment confirmed working
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/providers")
def provider_health():
    from providers.health_monitor import health_monitor
    from providers.cache_service import cache_service
    return {
        "providers": health_monitor.get_all_stats(),
        "cache": cache_service.stats(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/test/provider/{ticker}")
async def test_provider(ticker: str):
    from providers.market_data_service import market_data_service
    from providers.health_monitor import health_monitor
    from providers.cache_service import cache_service

    overview = await market_data_service.get_company_overview(ticker.upper())
    price    = await market_data_service.get_price_history(ticker.upper())

    return {
        "company": overview.model_dump(),
        "price_points": len(price.points),
        "latest_close": price.points[0].close if price.points else None,
        "provider_used": overview.provider,
        "provider_health": health_monitor.get_all_stats(),
        "cache_stats": cache_service.stats(),
    }

@app.get("/test/analytics/{ticker}")
async def test_analytics(ticker: str):
    from providers.market_data_service import market_data_service
    from analytics.technical_indicator_service import technical_indicator_service
    from analytics.financial_analysis_service import financial_analysis_service
    from analytics.news_aggregation_service import news_aggregation_service
    from analytics.sector_comparison_service import sector_comparison_service
    import dataclasses

    ticker = ticker.upper()

    overview  = await market_data_service.get_company_overview(ticker)
    prices    = await market_data_service.get_price_history(ticker)
    income    = await market_data_service.get_income_statement(ticker)
    balance   = await market_data_service.get_balance_sheet(ticker)
    cashflow  = await market_data_service.get_cash_flow(ticker)

    technical = technical_indicator_service.compute(prices)
    financial = financial_analysis_service.compute(
        overview, income, balance, cashflow
    )
    news      = await news_aggregation_service.get_company_news(
        ticker, overview.name
    )
    sentiment = news_aggregation_service.compute_sentiment_summary(news)
    sector    = await sector_comparison_service.compare(
        ticker, overview.sector
    )

    return {
        "technical": dataclasses.asdict(technical),
        "financial": dataclasses.asdict(financial),
        "news_count": len(news),
        "sentiment": sentiment,
        "sector": dataclasses.asdict(sector),
    }

@app.get("/test/finnhub/{ticker}")
async def test_finnhub(ticker: str):
    from providers.finnhub_provider import FinnhubProvider

    provider = FinnhubProvider()
    ticker = ticker.upper()

    try:
        overview     = await provider.get_company_overview(ticker)
        quote        = await provider.get_realtime_quote(ticker)
        try:
            prices = await provider.get_price_history(ticker)
        except Exception as e:
            prices = None
            print(f"Candles failed (expected on free tier): {e}")
        news         = await provider.get_news(ticker, limit=10)
        insider      = await provider.get_insider_trades(ticker, limit=10)
        peers        = await provider.get_peers(ticker)
        recs         = await provider.get_recommendations(ticker)
        sentiment    = await provider.get_sentiment_summary(ticker)
    finally:
        await provider.close()

    return {
        "overview":    overview.model_dump(),
        "realtime":    quote.model_dump(),
        "price_points": len(prices.points) if prices else 0,
        "latest_close": prices.points[0].close if (prices and prices.points) else None,
        "news_count":  len(news),
        "first_headline": news[0].title if news else None,
        "insider_count": len(insider),
        "first_insider":  insider[0].model_dump() if insider else None,
        "peers":          peers,
        "recommendations": recs.model_dump() if recs else None,
        "sentiment":       sentiment.model_dump() if sentiment else None,
    }


@app.get("/test/fmp/{ticker}")
async def test_fmp(ticker: str):
    from providers.fmp_provider import FMPProvider

    provider = FMPProvider()
    ticker = ticker.upper()

    try:
        overview = await provider.get_company_overview(ticker)
        income   = await provider.get_income_statement(ticker)
        balance  = await provider.get_balance_sheet(ticker)
        cashflow = await provider.get_cash_flow(ticker)
    finally:
        await provider.close()

    return {
        "overview":   overview.model_dump(),
        "income":     income.model_dump()   if income   else None,
        "balance":    balance.model_dump()  if balance  else None,
        "cashflow":   cashflow.model_dump() if cashflow else None,
    }


@app.get("/quotes/batch")
async def get_batch_quotes(tickers: str):
    """
    Returns realtime quotes for multiple tickers.
    Usage: /quotes/batch?tickers=AAPL,MSFT,GOOGL,TSLA,NVDA
    """
    from providers.market_data_service import market_data_service
    import asyncio

    symbols = [t.strip().upper() for t in tickers.split(",") if t.strip()][:20]
    results = await asyncio.gather(*[
        market_data_service.get_realtime_quote(s)
        for s in symbols
    ], return_exceptions=True)

    return {
        "quotes": [
            r.model_dump() for r in results
            if not isinstance(r, Exception)
        ],
        "failed": [
            s for s, r in zip(symbols, results)
            if isinstance(r, Exception)
        ],
    }

@app.get("/news/market")
async def get_market_news(limit: int = 8):
    """
    Fetches general market news from Finnhub.
    Not ticker-specific — broad market headlines.
    """
    from providers.finnhub_provider import FinnhubProvider
    import asyncio

    provider = FinnhubProvider()
    try:
        data = await provider._get("/news", {"category": "general", "minId": 0})
        articles = data if isinstance(data, list) else []
        news = []
        for a in articles[:limit]:
            try:
                import time as _time
                pub_ts  = a.get("datetime", 0)
                ago_sec = int(_time.time()) - pub_ts
                if ago_sec < 3600:
                    ago = f"{ago_sec // 60}m ago"
                elif ago_sec < 86400:
                    ago = f"{ago_sec // 3600}h ago"
                else:
                    ago = f"{ago_sec // 86400}d ago"

                category = a.get("category", "general").upper()

                news.append({
                    "headline": a.get("headline", ""),
                    "summary":  a.get("summary", ""),
                    "source":   a.get("source", ""),
                    "url":      a.get("url", ""),
                    "category": category,
                    "ago":      ago,
                    "image":    a.get("image", ""),
                })
            except Exception:
                continue
        return {"articles": news}
    finally:
        await provider.close()

@app.get("/market/sentiment")
async def get_market_sentiment():
    import asyncio, httpx, time as _time

    ALL_TICKERS = ["SPY", "QQQ", "VXX", "AAPL", "MSFT", "NVDA",
                   "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "JNJ"]
    BREADTH_TICKERS = ["AAPL","MSFT","NVDA","GOOGL","AMZN",
                       "META","TSLA","JPM","V","JNJ"]

    # Reuse market_data_service realtime quotes with health monitoring
    from providers.market_data_service import market_data_service

    results = await asyncio.gather(*[
        market_data_service.get_realtime_quote(t)
        for t in ALL_TICKERS
    ], return_exceptions=True)

    quotes = {}
    for ticker, result in zip(ALL_TICKERS, results):
        if not isinstance(result, Exception):
            quotes[ticker] = result

    score = 50.0
    signals = {}
    breadth_pct = None

    # Signal 1: VIX via VXX
    vxx = quotes.get("VXX")
    if vxx:
        p = vxx.current_price
        if p < 15:   score += 25; signals["volatility"] = "Extremely Low"
        elif p < 20: score += 15; signals["volatility"] = "Low"
        elif p < 25: score += 5;  signals["volatility"] = "Moderate"
        elif p < 30: score -= 10; signals["volatility"] = "Elevated"
        else:        score -= 20; signals["volatility"] = "High"

    # Signal 2: SPY momentum
    spy = quotes.get("SPY")
    if spy:
        pct = spy.percent_change
        score += min(15, max(-15, pct * 4))
        if pct > 1.0:    signals["momentum"] = "Strong"
        elif pct > 0.2:  signals["momentum"] = "Positive"
        elif pct > -0.2: signals["momentum"] = "Neutral"
        elif pct > -1.0: signals["momentum"] = "Negative"
        else:            signals["momentum"] = "Weak"

    # Signal 3: Market breadth from screener stocks
    breadth_quotes = [quotes[t] for t in BREADTH_TICKERS if t in quotes]
    if breadth_quotes:
        up_count = sum(1 for q in breadth_quotes if q.percent_change > 0)
        breadth_pct = up_count / len(breadth_quotes)
        score += (breadth_pct - 0.5) * 20
        if breadth_pct >= 0.7:   signals["breadth"] = "Broad Advance"
        elif breadth_pct >= 0.5: signals["breadth"] = "Positive"
        elif breadth_pct >= 0.3: signals["breadth"] = "Narrow"
        else:                     signals["breadth"] = "Broad Decline"

    # Signal 4: NASDAQ vs SPY risk appetite
    qqq = quotes.get("QQQ")
    if qqq and spy:
        diff = qqq.percent_change - spy.percent_change
        score += min(10, max(-10, diff * 5))
        if diff > 0.3:   signals["risk_appetite"] = "Risk-On"
        elif diff < -0.3: signals["risk_appetite"] = "Risk-Off"
        else:             signals["risk_appetite"] = "Neutral"

    final_score = max(0, min(100, round(score)))
    if final_score <= 25:   label = "Extreme Fear"
    elif final_score <= 45: label = "Fear"
    elif final_score <= 55: label = "Neutral"
    elif final_score <= 75: label = "Greed"
    else:                   label = "Extreme Greed"

    return {
        "score": final_score,
        "label": label,
        "signals": signals,
        "inputs": {
            "vxx_price":  vxx.current_price if vxx else None,
            "spy_change": spy.percent_change if spy else None,
            "breadth_pct": round(breadth_pct * 100, 1) if breadth_pct else None,
        }
    }

# ── Agent Orchestration Endpoint ─────────────────────────────────

@app.get("/narrative/{ticker}")
async def get_narrative_timeline(
    ticker: str,
    force_refresh: bool = False
):
    """
    Returns longitudinal narrative signals for a ticker.
    First call: downloads + processes SEC filings (30-60 seconds).
    Subsequent calls: returns from SQLite cache (instant).
    """
    from narrative.narrative_service import narrative_service
    import dataclasses

    signals = await narrative_service.get_narrative_timeline(
        ticker.upper(), force_refresh
    )

    if not signals:
        return {
            "ticker": ticker.upper(),
            "quarters": [],
            "message": "No filings found. Try a major US ticker like AAPL or MSFT."
        }

    return {
        "ticker":   ticker.upper(),
        "quarters": [dataclasses.asdict(s) for s in signals],
        "summary": {
            "total_quarters": len(signals),
            "tone_trend": [s.management_tone for s in signals],
            "ai_trend":   [s.ai_monetization for s in signals],
            "margin_trend": [s.margin_language for s in signals],
        }
    }


@app.get("/narrative/{ticker}/preprocess")
async def preprocess_narrative(ticker: str):
    """
    Pre-processes filings in the background.
    Call this for AAPL, NVDA, MSFT, META before the demo
    so the timeline loads instantly.
    """
    from narrative.narrative_service import narrative_service
    import asyncio

    async def background_process():
        await narrative_service.get_narrative_timeline(
            ticker.upper(), force_refresh=True
        )

    asyncio.create_task(background_process())
    return {
        "message": f"Processing {ticker.upper()} in background. "
                   f"Check /narrative/{ticker} in ~60 seconds."
    }

@app.get("/recommendations/{ticker}")
async def get_recommendations(ticker: str):
    from providers.market_data_service import market_data_service
    result = await market_data_service.get_recommendations(ticker.upper())
    if not result:
        return {"error": "No recommendations available"}
    return result.model_dump()

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
            data = result.model_dump()
            data["agent"] = name
            yield f"event: agent_complete\ndata: {json.dumps(data)}\n\n"
                
        # Now run the synthesis agent
        try:
            synthesis_agent = SynthesisAgent(ticker)
            synthesis_result = await synthesis_agent.analyze(results)
            
            synthesis_data = synthesis_result.model_dump()
            yield f"event: report_complete\ndata: {json.dumps(synthesis_data)}\n\n"
        except Exception as e:
            logger.error(f"Error in synthesis agent: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

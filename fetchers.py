"""
data/fetchers.py
All raw data fetching from external sources.
Each function is independent — can be called and tested individually.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yfinance as yf
import pandas as pd
import requests

from schemas import StockInfo, NewsArticle, InsiderTrade

logger = logging.getLogger(__name__)

# Directory where SEC filings get saved to disk
SEC_DOWNLOAD_DIR = Path("sec_filings")
SEC_DOWNLOAD_DIR.mkdir(exist_ok=True)


# ── yfinance ─────────────────────────────────────────────────────

yf_session = requests.Session()
yf_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})

def yf_retry(func):
    def wrapper(*args, **kwargs):
        retries = 3
        delay = 2
        for attempt in range(retries + 1):
            try:
                time.sleep(1)
                return func(*args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "too many requests" in err_str or "rate limit" in err_str or "expecting value" in err_str or "no price history found" in err_str:
                    logger.warning(f"[yfinance] Rate limit hit in {func.__name__}. Falling back to Alpha Vantage.")
                    return _av_fallback_router(func.__name__, *args, **kwargs)
                
                if attempt == retries:
                    raise
                logger.warning(f"[yfinance] Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
    return wrapper

@yf_retry
def fetch_stock_info(ticker: str) -> StockInfo:
    """
    Fetch company fundamentals and current price from Yahoo Finance.
    Returns a clean StockInfo object — no raw yfinance noise.
    """
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        info = stock.info

        return StockInfo(
            ticker=ticker.upper(),
            name=info.get("longName") or info.get("shortName", ticker),
            sector=info.get("sector", "Unknown"),
            industry=info.get("industry", "Unknown"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            price_to_book=info.get("priceToBook"),
            debt_to_equity=info.get("debtToEquity"),
            return_on_equity=info.get("returnOnEquity"),
            revenue_growth=info.get("revenueGrowth"),
            earnings_growth=info.get("earningsGrowth"),
            current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            description=info.get("longBusinessSummary"),
        )
    except Exception as e:
        logger.error(f"[yfinance] Failed to fetch info for {ticker}: {e}")
        raise


@yf_retry
def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch OHLCV price history.
    period options: 1mo, 3mo, 6mo, 1y, 2y, 5y
    Returns a DataFrame with columns: Open, High, Low, Close, Volume
    """
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        history = stock.history(period=period)
        if history.empty:
            raise ValueError(f"No price history found for {ticker}")
        return history
    except Exception as e:
        logger.error(f"[yfinance] Failed to fetch history for {ticker}: {e}")
        raise


@yf_retry
def fetch_financials(ticker: str) -> dict:
    """
    Fetch income statement, balance sheet, and cash flow.
    Returns a dict with keys: income_stmt, balance_sheet, cash_flow
    Each is a dict (converted from pandas DataFrame).
    """
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        return {
            "income_stmt": stock.financials.to_dict() if not stock.financials.empty else {},
            "balance_sheet": stock.balance_sheet.to_dict() if not stock.balance_sheet.empty else {},
            "cash_flow": stock.cashflow.to_dict() if not stock.cashflow.empty else {},
        }
    except Exception as e:
        logger.error(f"[yfinance] Failed to fetch financials for {ticker}: {e}")
        return {"income_stmt": {}, "balance_sheet": {}, "cash_flow": {}}


# ── SEC EDGAR ─────────────────────────────────────────────────────

def get_sec_headers() -> dict:
    email = os.getenv("SEC_EMAIL", "stocklens@example.com")
    return {"User-Agent": f"StockLens {email}"}

def fetch_sec_filings(ticker: str) -> dict:
    """
    Download the latest 10-K (annual), 2 10-Qs (quarterly),
    and up to 20 Form 4s (insider trades) from SEC EDGAR directly using requests.
    Files are saved to ./sec_filings/{ticker}/{form_type}/{accession}/.
    Returns paths to downloaded files.
    """
    ticker = ticker.upper()
    downloaded = {"10-K": [], "10-Q": [], "4": []}
    headers = get_sec_headers()

    try:
        # 1. Fetch CIK for the ticker
        tickers_resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=10)
        tickers_resp.raise_for_status()
        tickers_data = tickers_resp.json()
        
        cik_str = None
        for key, value in tickers_data.items():
            if value.get("ticker", "").upper() == ticker:
                cik_str = str(value.get("cik_str")).zfill(10)
                break
                
        if not cik_str:
            logger.warning(f"[SEC] CIK not found for {ticker}")
            return downloaded

        time.sleep(0.15)  # SEC Rate Limit: 10 requests / second max

        # 2. Fetch submissions for the CIK
        sub_resp = requests.get(f"https://data.sec.gov/submissions/CIK{cik_str}.json", headers=headers, timeout=10)
        sub_resp.raise_for_status()
        sub_data = sub_resp.json()
        recent = sub_data.get("filings", {}).get("recent", {})
        
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        
        limits = {"10-K": 1, "10-Q": 2, "4": 20}
        counts = {"10-K": 0, "10-Q": 0, "4": 0}
        
        for i in range(len(forms)):
            form_type = forms[i]
            if form_type in limits and counts[form_type] < limits[form_type]:
                accession = accessions[i]
                primary_doc = primary_docs[i]
                if not primary_doc:
                    continue
                
                acc_no_dashes = accession.replace("-", "")
                cik_stripped = cik_str.lstrip('0')
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_stripped}/{acc_no_dashes}/{primary_doc}"
                
                target_dir = SEC_DOWNLOAD_DIR / ticker / form_type / accession
                target_path = target_dir / primary_doc
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not target_path.exists():
                    time.sleep(0.15)
                    try:
                        doc_resp = requests.get(doc_url, headers=headers, timeout=10)
                        doc_resp.raise_for_status()
                        with open(target_path, "wb") as f:
                            f.write(doc_resp.content)
                        logger.info(f"[SEC] Downloaded {form_type} for {ticker} ({accession})")
                    except Exception as e:
                        logger.warning(f"[SEC] Failed to download {form_type} doc {doc_url}: {e}")
                
                counts[form_type] += 1

        downloaded["10-K"] = _list_filing_paths(ticker, "10-K")
        downloaded["10-Q"] = _list_filing_paths(ticker, "10-Q")
        downloaded["4"] = _list_filing_paths(ticker, "4")
        
    except Exception as e:
        logger.warning(f"[SEC] Fetch failed for {ticker}: {e}")

    return downloaded


def _list_filing_paths(ticker: str, form_type: str) -> list[str]:
    """Return paths of all downloaded files for a given ticker and form type."""
    base = SEC_DOWNLOAD_DIR / ticker.upper() / form_type
    if not base.exists():
        return []
    paths = []
    for filing_dir in sorted(base.iterdir(), reverse=True):
        for file in filing_dir.rglob("*.htm"):
            paths.append(str(file))
        for file in filing_dir.rglob("*.html"):
            paths.append(str(file))
        for file in filing_dir.rglob("*.xml"):
            paths.append(str(file))
    return paths


def read_filing_text(file_path: str, max_chars: int = 50_000) -> str:
    """
    Read raw text from a downloaded SEC filing.
    Strips excessive whitespace. Caps at max_chars to stay within LLM context.
    """
    try:
        from bs4 import BeautifulSoup
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
        if file_path.endswith(".htm"):
            soup = BeautifulSoup(raw, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
        else:
            text = raw
        # Collapse whitespace
        import re
        text = re.sub(r"\s+", " ", text)
        return text[:max_chars]
    except Exception as e:
        logger.error(f"[SEC] Failed to read {file_path}: {e}")
        return ""


def parse_insider_trades(ticker: str) -> list[InsiderTrade]:
    """
    Parse Form 4 XML files to extract insider buy/sell transactions.
    Returns a list of InsiderTrade objects.
    """
    import xml.etree.ElementTree as ET

    form4_paths = _list_filing_paths(ticker, "4")
    trades = []

    for path in form4_paths:
        if not path.endswith(".xml"):
            continue
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            # Extract filer name
            filer_name = ""
            for elem in root.iter("rptOwnerName"):
                filer_name = elem.text or ""
                break

            # Extract transactions
            for txn in root.iter("nonDerivativeTransaction"):
                txn_code = txn.find(".//transactionCode")
                shares_elem = txn.find(".//transactionShares/value")
                price_elem = txn.find(".//transactionPricePerShare/value")
                date_elem = txn.find(".//transactionDate/value")

                if txn_code is None or shares_elem is None:
                    continue

                code = txn_code.text or ""
                txn_type = "Buy" if code == "P" else "Sell" if code == "S" else code

                try:
                    shares = float(shares_elem.text or 0)
                    price = float(price_elem.text) if price_elem is not None else None
                    date = date_elem.text if date_elem is not None else ""

                    trades.append(InsiderTrade(
                        filer_name=filer_name,
                        transaction_type=txn_type,
                        shares=shares,
                        price_per_share=price,
                        date=date,
                    ))
                except (ValueError, TypeError):
                    continue

        except Exception as e:
            logger.warning(f"[SEC] Failed to parse Form 4 at {path}: {e}")

    return trades


# ── NewsAPI ───────────────────────────────────────────────────────

def fetch_news(ticker: str, company_name: str, days_back: int = 30) -> list[NewsArticle]:
    """
    Fetch recent news articles about the company from NewsAPI.
    Falls back to a free RSS approach if no API key is set.
    """
    api_key = os.getenv("NEWS_API_KEY", "")

    if api_key:
        return _fetch_news_api(company_name, api_key, days_back)
    else:
        logger.warning("[NewsAPI] No API key found — falling back to Yahoo Finance news")
        return _fetch_yahoo_news(ticker)


def _fetch_news_api(company_name: str, api_key: str, days_back: int) -> list[NewsArticle]:
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "from": from_date,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 30,
        "apiKey": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [
            NewsArticle(
                title=a.get("title", ""),
                description=a.get("description"),
                content=a.get("content"),
                url=a.get("url", ""),
                published_at=a.get("publishedAt", ""),
                source=a.get("source", {}).get("name", "Unknown"),
            )
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
    except Exception as e:
        logger.error(f"[NewsAPI] Request failed: {e}")
        return []


@yf_retry
def _fetch_yahoo_news(ticker: str) -> list[NewsArticle]:
    """Fallback: grab news directly from Yahoo Finance via yfinance."""
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        news = stock.news or []
        articles = []
        for item in news[:20]:
            articles.append(NewsArticle(
                title=item.get("title", ""),
                description=item.get("summary", ""),
                content=item.get("summary", ""),
                url=item.get("link", ""),
                published_at=datetime.fromtimestamp(
                    item.get("providerPublishTime", 0)
                ).isoformat(),
                source=item.get("publisher", "Yahoo Finance"),
            ))
        return articles
    except Exception as e:
        logger.error(f"[Yahoo News] Failed for {ticker}: {e}")
        return []


# ── Peer / macro ──────────────────────────────────────────────────

@yf_retry
def fetch_peers(ticker: str) -> list[str]:
    """
    Get a list of peer tickers in the same sector.
    Uses a hardcoded map for common sectors + yfinance as fallback.
    """
    sector_peers = {
        "Technology": ["MSFT", "GOOGL", "META", "NVDA", "AMD"],
        "Consumer Cyclical": ["AMZN", "TSLA", "NKE", "MCD", "SBUX"],
        "Healthcare": ["JNJ", "PFE", "MRK", "ABBV", "UNH"],
        "Financials": ["JPM", "BAC", "GS", "MS", "WFC"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
        "Industrials": ["CAT", "BA", "GE", "HON", "UPS"],
    }
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        sector = stock.info.get("sector", "")
        peers = sector_peers.get(sector, [])
        # Remove the ticker itself
        return [p for p in peers if p.upper() != ticker.upper()][:4]
    except Exception:
        return []


@yf_retry
def fetch_sector_etf_performance(ticker: str) -> dict:
    """
    Compare the ticker's 3-month return vs its sector ETF.
    """
    sector_etf_map = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Cyclical": "XLY",
        "Industrials": "XLI",
        "Real Estate": "XLRE",
        "Utilities": "XLU",
        "Materials": "XLB",
        "Communication Services": "XLC",
        "Consumer Defensive": "XLP",
    }
    try:
        stock = yf.Ticker(ticker, session=yf_session)
        sector = stock.info.get("sector", "")
        etf_ticker = sector_etf_map.get(sector, "SPY")

        hist_stock = yf.download(ticker, period="3mo", progress=False, session=yf_session)["Close"]
        time.sleep(1)
        hist_etf = yf.download(etf_ticker, period="3mo", progress=False, session=yf_session)["Close"]

        if hist_stock.empty or hist_etf.empty:
            return {}

        stock_return = float((hist_stock.iloc[-1] - hist_stock.iloc[0]) / hist_stock.iloc[0] * 100)
        etf_return = float((hist_etf.iloc[-1] - hist_etf.iloc[0]) / hist_etf.iloc[0] * 100)

        return {
            "ticker_3mo_return": round(stock_return, 2),
            "sector_etf": etf_ticker,
            "sector_etf_3mo_return": round(etf_return, 2),
            "outperformance": round(stock_return - etf_return, 2),
        }
    except Exception as e:
        logger.error(f"[Macro] Sector ETF comparison failed: {e}")
        return {}


# ── Alpha Vantage Fallback ───────────────────────────────────────

def _av_fallback_router(func_name, *args, **kwargs):
    if func_name == "fetch_stock_info": return _av_fetch_stock_info(*args, **kwargs)
    elif func_name == "fetch_price_history": return _av_fetch_price_history(*args, **kwargs)
    elif func_name == "fetch_financials": return _av_fetch_financials(*args, **kwargs)
    elif func_name == "fetch_sector_etf_performance": return _av_fetch_sector_etf_performance(*args, **kwargs)
    elif func_name == "fetch_peers": return _av_fetch_peers(*args, **kwargs)
    elif func_name == "_fetch_yahoo_news": return _av_fetch_yahoo_news(*args, **kwargs)
    else: raise NotImplementedError(f"No AV fallback for {func_name}")

def _av_fetch_stock_info(ticker: str) -> StockInfo:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    resp = requests.get(f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}").json()
    if "Symbol" not in resp: raise ValueError(f"Alpha Vantage OVERVIEW failed: {resp}")
    
    q_resp = requests.get(f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={api_key}").json()
    quote = q_resp.get("Global Quote", {})
    current_price = float(quote.get("05. price", 0))

    def safe_float(val):
        try: return float(val)
        except: return None

    return StockInfo(
        ticker=ticker.upper(),
        name=resp.get("Name", ticker),
        sector=resp.get("Sector", "Unknown"),
        industry=resp.get("Industry", "Unknown"),
        market_cap=safe_float(resp.get("MarketCapitalization")),
        pe_ratio=safe_float(resp.get("PERatio")),
        forward_pe=safe_float(resp.get("ForwardPE")),
        price_to_book=safe_float(resp.get("PriceToBookRatio")),
        debt_to_equity=None,
        return_on_equity=safe_float(resp.get("ReturnOnEquityTTM")),
        revenue_growth=safe_float(resp.get("RevenueGrowthYOY")),
        earnings_growth=safe_float(resp.get("QuarterlyEarningsGrowthYOY")),
        current_price=current_price,
        fifty_two_week_high=safe_float(resp.get("52WeekHigh")),
        fifty_two_week_low=safe_float(resp.get("52WeekLow")),
        description=resp.get("Description", "")
    )

def _av_fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    resp = requests.get(f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=compact&apikey={api_key}").json()
    ts = resp.get("Time Series (Daily)", {})
    if not ts: raise ValueError(f"Alpha Vantage TIME_SERIES_DAILY failed: {resp}")
    
    df = pd.DataFrame.from_dict(ts, orient="index")
    df.index = pd.to_datetime(df.index)
    df = df.rename(columns={"1. open": "Open", "2. high": "High", "3. low": "Low", "4. close": "Close", "5. volume": "Volume"}).astype(float)
    df = df.sort_index()

    now = pd.Timestamp.now().normalize()
    if period == "1mo": start = now - pd.DateOffset(months=1)
    elif period == "3mo": start = now - pd.DateOffset(months=3)
    elif period == "6mo": start = now - pd.DateOffset(months=6)
    elif period == "1y": start = now - pd.DateOffset(years=1)
    elif period == "2y": start = now - pd.DateOffset(years=2)
    elif period == "5y": start = now - pd.DateOffset(years=5)
    else: start = now - pd.DateOffset(years=1)
    
    return df[df.index >= start]

def _av_fetch_financials(ticker: str) -> dict:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    def fetch_stmt(func):
        resp = requests.get(f"https://www.alphavantage.co/query?function={func}&symbol={ticker}&apikey={api_key}").json()
        reports = resp.get("annualReports", [])
        if not reports: return pd.DataFrame()
        return pd.DataFrame(reports).set_index("fiscalDateEnding").transpose()

    return {
        "income_stmt": fetch_stmt("INCOME_STATEMENT").to_dict(),
        "balance_sheet": fetch_stmt("BALANCE_SHEET").to_dict(),
        "cash_flow": fetch_stmt("CASH_FLOW").to_dict()
    }

def _av_fetch_sector_etf_performance(ticker: str) -> dict:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    resp = requests.get(f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}").json()
    sector = resp.get("Sector", "")
    
    sector_etf_map = {
        "TECHNOLOGY": "XLK", "HEALTHCARE": "XLV", "FINANCE": "XLF", "FINANCIALS": "XLF",
        "ENERGY": "XLE", "CONSUMER DURABLES": "XLY", "CONSUMER NON-DURABLES": "XLP",
        "CAPITAL GOODS": "XLI", "REAL ESTATE": "XLRE", "PUBLIC UTILITIES": "XLU",
        "BASIC INDUSTRIES": "XLB", "TECHNOLOGY SERVICES": "XLC",
    }
    etf_ticker = sector_etf_map.get(sector.upper(), "SPY")
    
    hist_stock = _av_fetch_price_history(ticker, period="3mo")["Close"]
    import time
    time.sleep(1)
    hist_etf = _av_fetch_price_history(etf_ticker, period="3mo")["Close"]
    
    if len(hist_stock) < 2 or len(hist_etf) < 2:
        return {"stock_3mo_return": 0.0, "etf_3mo_return": 0.0}
    
    return {
        "stock_3mo_return": float((hist_stock.iloc[-1] - hist_stock.iloc[0]) / hist_stock.iloc[0]),
        "etf_3mo_return": float((hist_etf.iloc[-1] - hist_etf.iloc[0]) / hist_etf.iloc[0])
    }

def _av_fetch_peers(ticker: str) -> list[str]:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    resp = requests.get(f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={api_key}").json()
    sector = resp.get("Sector", "")
    
    av_to_std = {
        "TECHNOLOGY": "Technology", "HEALTHCARE": "Healthcare", "FINANCE": "Financials",
        "ENERGY": "Energy", "CONSUMER DURABLES": "Consumer Cyclical", "CAPITAL GOODS": "Industrials",
    }
    std_sector = av_to_std.get(sector.upper(), "Technology")
    sector_peers = {
        "Technology": ["MSFT", "GOOGL", "META", "NVDA", "AMD"],
        "Consumer Cyclical": ["AMZN", "TSLA", "NKE", "MCD", "SBUX"],
        "Healthcare": ["JNJ", "PFE", "MRK", "ABBV", "UNH"],
        "Financials": ["JPM", "BAC", "GS", "MS", "WFC"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
        "Industrials": ["CAT", "BA", "GE", "HON", "UPS"],
    }
    peers = sector_peers.get(std_sector, ["MSFT", "AAPL"])
    if ticker in peers: peers.remove(ticker)
    return peers[:5]

def _av_fetch_yahoo_news(ticker: str) -> list[NewsArticle]:
    api_key = os.getenv("ALPHA_VANTAGE_KEY")
    resp = requests.get(f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={ticker}&limit=10&apikey={api_key}").json()
    
    articles = []
    for item in resp.get("feed", []):
        t = item.get("time_published", "")
        pub_date = t if not t else f"{t[:4]}-{t[4:6]}-{t[6:8]}T{t[9:11]}:{t[11:13]}:{t[13:15]}Z"
        articles.append(NewsArticle(
            title=item.get("title", ""),
            publisher=item.get("source", ""),
            link=item.get("url", ""),
            published_at=pub_date,
            description=item.get("summary", "")
        ))
    return articles

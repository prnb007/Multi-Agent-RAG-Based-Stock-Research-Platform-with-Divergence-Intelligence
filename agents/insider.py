import logging
import os
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from agents.base import BaseAgent, AgentOutput, call_llm

logger = logging.getLogger(__name__)

# --- Copied SEC Logic ---
class InsiderTrade(BaseModel):
    filer_name: str
    transaction_type: str
    shares: float
    price_per_share: Optional[float]
    date: str

SEC_DOWNLOAD_DIR = Path("sec_filings")
SEC_DOWNLOAD_DIR.mkdir(exist_ok=True)

def get_sec_headers() -> dict:
    email = os.getenv("SEC_EMAIL", "stocklens@example.com")
    return {"User-Agent": f"StockLens {email}"}

def _list_filing_paths(ticker: str, form_type: str) -> list[str]:
    base = SEC_DOWNLOAD_DIR / ticker.upper() / form_type
    if not base.exists():
        return []
    paths = []
    for filing_dir in sorted(base.iterdir(), reverse=True):
        for file in filing_dir.rglob("*.xml"):
            paths.append(str(file))
    return paths

def fetch_sec_filings(ticker: str) -> dict:
    ticker = ticker.upper()
    downloaded = {"4": []}
    headers = get_sec_headers()

    try:
        tickers_resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=10)
        tickers_resp.raise_for_status()
        tickers_data = tickers_resp.json()
        
        cik_str = None
        for key, value in tickers_data.items():
            if value.get("ticker", "").upper() == ticker:
                cik_str = str(value.get("cik_str")).zfill(10)
                break
                
        if not cik_str:
            return downloaded

        time.sleep(0.15)
        sub_resp = requests.get(f"https://data.sec.gov/submissions/CIK{cik_str}.json", headers=headers, timeout=10)
        sub_resp.raise_for_status()
        sub_data = sub_resp.json()
        recent = sub_data.get("filings", {}).get("recent", {})
        
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        
        counts = {"4": 0}
        
        for i in range(len(forms)):
            form_type = forms[i]
            if form_type == "4" and counts["4"] < 20:
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
                    except Exception:
                        pass
                
                counts["4"] += 1

        downloaded["4"] = _list_filing_paths(ticker, "4")
        
    except Exception as e:
        logger.warning(f"[SEC] Fetch failed for {ticker}: {e}")

    return downloaded

def parse_insider_trades(ticker: str) -> list[InsiderTrade]:
    form4_paths = _list_filing_paths(ticker, "4")
    trades = []

    for path in form4_paths:
        if not path.endswith(".xml"):
            continue
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            filer_name = ""
            for elem in root.iter("rptOwnerName"):
                filer_name = elem.text or ""
                break

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

        except Exception:
            pass

    return trades


class InsiderAgent(BaseAgent):
    name = "insider"
    
    async def analyze(self) -> AgentOutput:
        logger.info(f"[{self.ticker}] InsiderAgent starting analysis...")
        try:
            fetch_sec_filings(self.ticker)
            trades = parse_insider_trades(self.ticker)
            
            if not trades:
                return AgentOutput(
                    agent=self.name,
                    score=0.0,
                    confidence=0.5,
                    summary="No recent insider trades found (Form 4).",
                    evidence=[]
                )
                
            trades_context = ""
            for t in trades[:30]:
                trades_context += f"Filer: {t.filer_name}, Type: {t.transaction_type}, Shares: {t.shares}, Price: {t.price_per_share}, Date: {t.date}\n"
            
            system_prompt = (
                "You are an expert insider trading analyst. Your job is to evaluate SEC Form 4 filings "
                "to determine if corporate insiders are buying or selling. Consider the buy/sell ratio, "
                "trade sizes, and recency. Return a JSON object with this exact shape: "
                '{{"score": <float -1.0 to 1.0>, "confidence": <float 0.0 to 1.0>, '
                '"summary": "<2-3 sentences>", "evidence": ["bullet 1", "bullet 2", ...]}}'
            )
            
            user_prompt = f"Analyze the recent insider trades for {self.ticker}:\n\n{trades_context}"
            
            result = await call_llm(system_prompt, user_prompt)
            
            return AgentOutput(
                agent=self.name,
                score=float(result.get("score", 0.0)),
                confidence=float(result.get("confidence", 0.7)),
                summary=result.get("summary", ""),
                evidence=result.get("evidence", [])
            )
            
        except Exception as e:
            logger.error(f"[{self.ticker}] InsiderAgent failed: {e}")
            return AgentOutput(
                agent=self.name,
                score=0.0,
                confidence=0.0,
                summary=f"Analysis failed: {str(e)}",
                evidence=[]
            )

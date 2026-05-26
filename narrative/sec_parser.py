"""
Downloads and parses 10-Q filings from SEC EDGAR.
Extracts the MD&A section — management's own words about the business.
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime
from sec_edgar_downloader import Downloader

logger = logging.getLogger(__name__)

SEC_EMAIL   = os.getenv("SEC_EMAIL", "research@stocklens.ai")
FILINGS_DIR = Path("sec_filings")


def download_10q_filings(ticker: str, num_quarters: int = 4) -> list[dict]:
    """
    Download last N quarters of 10-Q filings for a ticker.
    Returns list of {quarter, filing_date, text} dicts.
    """
    ticker = ticker.upper()
    dl = Downloader("StockLens", SEC_EMAIL, FILINGS_DIR)

    try:
        dl.get("10-Q", ticker, limit=num_quarters, download_details=True)
    except Exception as e:
        logger.warning(f"[SEC] Download failed for {ticker}: {e}")

    filings = []
    ticker_dir = FILINGS_DIR / "sec-edgar-filings" / ticker / "10-Q"
    if not ticker_dir.exists():
        logger.warning(f"[SEC] No 10-Q filings found for {ticker}")
        return filings

    # Each subdirectory is one filing
    filing_dirs = sorted(ticker_dir.iterdir(), reverse=True)[:num_quarters]

    for idx, filing_dir in enumerate(filing_dirs):
        try:
            text = _extract_text_from_filing(filing_dir)
            if not text:
                continue
            mda = _extract_mda_section(text)
            quarter = _infer_quarter_from_path(filing_dir, index=idx)
            filing_date = _infer_date_from_path(filing_dir)

            filings.append({
                "quarter":      quarter,
                "filing_date":  filing_date,
                "mda_text":     mda,
                "full_length":  len(mda),
            })
            logger.info(
                f"[SEC] {ticker} {quarter}: extracted "
                f"{len(mda):,} chars of MD&A"
            )
        except Exception as e:
            logger.warning(f"[SEC] Failed to parse filing {filing_dir}: {e}")
            continue

    return filings


def _extract_text_from_filing(filing_dir: Path) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return ""

    candidates = []
    for ext in [".htm", ".html"]:
        for f in filing_dir.rglob(f"*{ext}"):
            try:
                skip_names = ["filing-details", "index", "metalinks", "R1", "R2", "R3"]
                if any(s.lower() in f.name.lower() for s in skip_names):
                    continue
                candidates.append((f.stat().st_size, f))
            except Exception:
                continue

    candidates.sort(reverse=True)

    for _, f in candidates[:3]:
        try:
            raw = f.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(raw, "html.parser")
            for tag in soup(["script", "style", "ix:header", "head"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 8000:
                return text
        except Exception:
            continue
    return ""


def _extract_mda_section(text: str) -> str:
    # Hard stop before Internal Controls section
    for stop in [
        "CONTROLS AND PROCEDURES",
        "QUANTITATIVE AND QUALITATIVE DISCLOSURES",
        "Item 4", "ITEM 4",
    ]:
        pos = text.find(stop, 20000)
        if pos != -1:
            text = text[:pos]
            break

    # Find Results of Operations
    start_pos = None
    for pattern in [
        r"(?i)results\s+of\s+operations",
        r"(?i)revenue\s+recognition",
        r"(?i)net\s+revenue.{0,50}(increased|decreased|grew)",
        r"(?i)management.{0,30}discussion",
    ]:
        matches = list(re.finditer(pattern, text))
        valid_matches = [m for m in matches if m.start() > 20000]
        if valid_matches:
            start_pos = valid_matches[0].start()
            break

    if not start_pos:
        # Fallback to first third of document
        return text[:15000]

    end_pos = len(text)
    for pattern in [
        r"(?i)liquidity\s+and\s+capital",
        r"(?i)critical\s+accounting",
        r"(?i)off[\s\-]balance\s+sheet",
    ]:
        m = re.search(pattern, text[start_pos + 200:])
        if m:
            end_pos = start_pos + 200 + m.start()
            break

    return text[start_pos:end_pos][:15000]


def _infer_quarter_from_path(path: Path, index: int = 0) -> str:
    """
    Derives quarter from accession number year + filing order.
    Accession format: XXXXXXXXXX-YY-ZZZZZZ
    YY = 2-digit year of filing.
    index = 0 means most recent filing, 1 = one quarter ago, etc.
    """
    name = path.name  # e.g. "0000320193-25-000123"
    parts = name.split("-")

    try:
        year_short = parts[1]                    # "25"
        year = f"20{year_short}"                 # "2025"
    except (IndexError, ValueError):
        year = "2025"

    # Map index to quarter label
    # filings are sorted newest-first, so index 0 = most recent
    quarter_labels = ["Q4", "Q3", "Q2", "Q1"]
    q_label = quarter_labels[index] if index < 4 else f"Q{index + 1}"

    return f"{year}-{q_label}"


def _infer_date_from_path(path: Path) -> str:
    parts = path.name.split('-')
    if len(parts) >= 3:
        year = "20" + parts[1]
        return f"{year}-01-01"
    return "Unknown"

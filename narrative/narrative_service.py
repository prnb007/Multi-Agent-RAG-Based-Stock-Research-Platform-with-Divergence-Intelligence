"""
NarrativeService — orchestrates the full pipeline:
1. Check SQLite cache
2. Download 10-Q filings from SEC EDGAR
3. Extract MD&A sections
4. Run LLM signal extraction
5. Store in SQLite
6. Return time-series of signals
"""

import logging
import asyncio
from datetime import datetime
from narrative.models import (
    NarrativeSignal, save_signal,
    get_signals_for_ticker, ticker_is_cached
)
from narrative.sec_parser import download_10q_filings
from narrative.signal_extractor import extract_signals

logger = logging.getLogger(__name__)


class NarrativeService:

    async def get_narrative_timeline(
        self, ticker: str, force_refresh: bool = False
    ) -> list[NarrativeSignal]:
        """
        Main entry point. Returns time-series of signals for a ticker.
        Uses SQLite cache — only re-processes if not cached.
        """
        ticker = ticker.upper()

        if not force_refresh and ticker_is_cached(ticker):
            logger.info(f"[Narrative] {ticker}: returning cached signals")
            return get_signals_for_ticker(ticker)

        logger.info(f"[Narrative] {ticker}: processing filings...")
        filings = await asyncio.get_event_loop().run_in_executor(
            None, lambda: download_10q_filings(ticker, num_quarters=4)
        )

        if not filings:
            logger.warning(f"[Narrative] {ticker}: no filings found")
            return []

        # Extract signals for each quarter in parallel
        tasks = [
            extract_signals(ticker, f["quarter"], f["mda_text"])
            for f in filings
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        signals = []
        for filing, result in zip(filings, results):
            if isinstance(result, Exception):
                logger.error(
                    f"[Narrative] {ticker} {filing['quarter']} "
                    f"extraction failed: {result}"
                )
                continue

            signal = NarrativeSignal(
                ticker=ticker,
                quarter=filing["quarter"],
                filing_date=filing["filing_date"],
                management_tone=result.get("management_tone", "cautious"),
                margin_language=result.get("margin_language", "stable"),
                ai_monetization=result.get("ai_monetization", "absent"),
                demand_signals=result.get("demand_signals", "mixed"),
                hiring_language=result.get("hiring_language", "stable"),
                regulatory_concern=result.get("regulatory_concern", "moderate"),
                recurring_concerns=result.get("recurring_concerns", []),
                key_quotes=result.get("key_quotes", []),
                confidence=float(result.get("confidence", 0.5)),
                raw_text_length=filing["full_length"],
                processed_at=datetime.utcnow().isoformat(),
            )
            save_signal(signal)
            signals.append(signal)

        logger.info(
            f"[Narrative] {ticker}: processed "
            f"{len(signals)} quarters successfully"
        )
        return get_signals_for_ticker(ticker)


narrative_service = NarrativeService()

"""
SectorComparisonService
Computes relative strength vs sector ETF and peers.
Used by MacroAgent.
"""

import logging
import asyncio
from dataclasses import dataclass
from typing import Optional
from providers.market_data_service import market_data_service

logger = logging.getLogger(__name__)

SECTOR_ETF_MAP = {
    "TECHNOLOGY": "XLK",
    "HEALTH CARE": "XLV",
    "FINANCIALS": "XLF",
    "ENERGY": "XLE",
    "CONSUMER DISCRETIONARY": "XLY",
    "CONSUMER STAPLES": "XLP",
    "INDUSTRIALS": "XLI",
    "REAL ESTATE": "XLRE",
    "UTILITIES": "XLU",
    "MATERIALS": "XLB",
    "COMMUNICATION SERVICES": "XLC",
}

SECTOR_PEERS = {
    "TECHNOLOGY": ["MSFT", "GOOGL", "META", "NVDA", "AMD"],
    "HEALTH CARE": ["JNJ", "PFE", "MRK", "ABBV", "UNH"],
    "FINANCIALS": ["JPM", "BAC", "GS", "MS", "WFC"],
    "ENERGY": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "CONSUMER DISCRETIONARY": ["AMZN", "TSLA", "NKE", "MCD", "SBUX"],
    "INDUSTRIALS": ["CAT", "BA", "GE", "HON", "UPS"],
    "COMMUNICATION SERVICES": ["GOOGL", "META", "NFLX", "DIS", "T"],
}


@dataclass
class SectorComparison:
    ticker: str
    sector: str
    sector_etf: Optional[str]
    ticker_3mo_return: Optional[float]
    etf_3mo_return: Optional[float]
    outperformance: Optional[float]      # ticker return - ETF return
    peer_tickers: list[str]
    peer_avg_return: Optional[float]
    vs_peers: Optional[float]            # ticker return - peer avg
    relative_strength: Optional[str]     # "strong" | "neutral" | "weak"
    macro_score: float                   # -1.0 to +1.0


class SectorComparisonService:

    def _compute_return(self, points: list) -> Optional[float]:
        if not points or len(points) < 2:
            return None
        sorted_pts = sorted(points, key=lambda p: p.date)
        # Use last 63 trading days (~3 months)
        window = sorted_pts[-63:] if len(sorted_pts) >= 63 else sorted_pts
        oldest = window[0].close
        latest = window[-1].close
        if oldest <= 0:
            return None
        return round((latest - oldest) / oldest * 100, 2)

    async def compare(
        self, ticker: str, sector: str
    ) -> SectorComparison:
        sector_upper = sector.upper()
        etf = SECTOR_ETF_MAP.get(sector_upper, "SPY")
        peers = [
            p for p in SECTOR_PEERS.get(sector_upper, [])
            if p.upper() != ticker.upper()
        ][:4]

        # Fetch ticker + ETF + peers in parallel
        fetch_targets = [ticker, etf] + peers
        results = await asyncio.gather(*[
            market_data_service.get_price_history(t)
            for t in fetch_targets
        ], return_exceptions=True)

        returns = {}
        for t, r in zip(fetch_targets, results):
            if not isinstance(r, Exception):
                returns[t] = self._compute_return(r.points)

        ticker_return = returns.get(ticker)
        etf_return    = returns.get(etf)
        peer_returns  = [
            returns[p] for p in peers
            if p in returns and returns[p] is not None
        ]

        outperformance = (
            round(ticker_return - etf_return, 2)
            if ticker_return is not None and etf_return is not None
            else None
        )
        peer_avg = (
            round(sum(peer_returns) / len(peer_returns), 2)
            if peer_returns else None
        )
        vs_peers = (
            round(ticker_return - peer_avg, 2)
            if ticker_return is not None and peer_avg is not None
            else None
        )

        # Relative strength label
        relative_strength = "neutral"
        if outperformance is not None:
            if outperformance > 5:
                relative_strength = "strong"
            elif outperformance < -5:
                relative_strength = "weak"

        # Macro score: -1.0 to +1.0
        score_parts = []
        if outperformance is not None:
            score_parts.append(max(-1.0, min(1.0, outperformance / 20)))
        if vs_peers is not None:
            score_parts.append(max(-1.0, min(1.0, vs_peers / 15)))

        macro_score = round(
            sum(score_parts) / len(score_parts) if score_parts else 0.0, 3
        )

        return SectorComparison(
            ticker=ticker,
            sector=sector,
            sector_etf=etf,
            ticker_3mo_return=ticker_return,
            etf_3mo_return=etf_return,
            outperformance=outperformance,
            peer_tickers=peers,
            peer_avg_return=peer_avg,
            vs_peers=vs_peers,
            relative_strength=relative_strength,
            macro_score=macro_score,
        )


sector_comparison_service = SectorComparisonService()

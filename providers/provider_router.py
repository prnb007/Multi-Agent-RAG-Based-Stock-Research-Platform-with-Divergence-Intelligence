"""
ProviderRouter — routes each data type to the correct primary provider,
with automatic fallback when a provider fails or is marked unhealthy.
"""

import logging
import time
from providers.alpha_vantage_provider import AlphaVantageProvider
from providers.finnhub_provider import FinnhubProvider
from providers.fmp_provider import FMPProvider
from providers.health_monitor import health_monitor

logger = logging.getLogger(__name__)


class ProviderRouter:
    """
    Routes each data method to its primary provider, then falls back through
    a configured chain. Each chain is data-type-specific.
    """

    # Provider chain per data method:
    # First provider in the list is primary, rest are fallbacks
    ROUTES = {
        # Financials → FMP primary (best statements), no fallback (premium quality only)
        "get_company_overview":  ["fmp", "finnhub"],
        "get_income_statement":  ["fmp"],
        "get_balance_sheet":     ["fmp"],
        "get_cash_flow":         ["fmp"],

        # OHLCV → Alpha Vantage primary (most reliable on free tier)
        "get_price_history":     ["alpha_vantage"],

        # Finnhub-exclusive data types
        "get_news":              ["finnhub", "alpha_vantage"],
        "get_insider_trades":    ["finnhub"],
        "get_peers":             ["finnhub"],
        "get_realtime_quote":    ["finnhub"],
        "get_recommendations":   ["finnhub"],
    }

    def __init__(self):
        self.providers = {
            "alpha_vantage": AlphaVantageProvider(),
            "finnhub":       FinnhubProvider(),
            "fmp":           FMPProvider(),
        }

    async def fetch(self, method: str, ticker: str, **kwargs):
        """
        Try each provider in this method's chain. Record success/failure
        in ProviderHealthMonitor. Raise if ALL providers in the chain fail.
        """
        chain = self.ROUTES.get(method)
        if not chain:
            raise ValueError(f"No route configured for method: {method}")

        last_error = None
        for provider_name in chain:
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            if not health_monitor.is_provider_healthy(provider_name):
                logger.warning(
                    f"[Router] Skipping {provider_name} — marked unhealthy"
                )
                continue

            if not hasattr(provider, method):
                logger.debug(
                    f"[Router] {provider_name} does not implement {method}"
                )
                continue

            start = time.time()
            try:
                fn = getattr(provider, method)
                result = await fn(ticker, **kwargs)
                latency = (time.time() - start) * 1000
                health_monitor.record_success(provider_name, latency)
                logger.info(
                    f"[Router] {method}({ticker}) ← {provider_name} in {latency:.0f}ms"
                )
                return result
            except Exception as e:
                last_error = e
                latency = (time.time() - start) * 1000
                error_type = (
                    "rate_limit" if "429" in str(e) or "rate limit" in str(e).lower()
                    else "timeout" if "timeout" in str(e).lower()
                    else "unknown"
                )
                health_monitor.record_failure(provider_name, error_type)
                logger.warning(
                    f"[Router] {provider_name} failed for {method}({ticker}): {e}"
                )

        raise RuntimeError(
            f"All providers in chain {chain} failed for {method}({ticker}). "
            f"Last error: {last_error}"
        )

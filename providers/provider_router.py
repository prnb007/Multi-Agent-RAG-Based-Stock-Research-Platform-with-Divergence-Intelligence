"""
ProviderRouter — decides which provider to use.
Always tries Alpha Vantage first. Falls back to yfinance on failure.
Extendable: add Polygon, FMP, Finnhub later by adding to the chain.
"""

import logging
import time
from providers.alpha_vantage_provider import AlphaVantageProvider
from providers.yfinance_provider import YFinanceProvider
from providers.health_monitor import health_monitor

logger = logging.getLogger(__name__)


class ProviderRouter:
    def __init__(self):
        self.primary  = AlphaVantageProvider()
        self.fallback = YFinanceProvider()

    async def fetch(self, method: str, ticker: str, **kwargs):
        """
        Try primary provider. On any failure, log it and try fallback.
        Automatically records success/failure in ProviderHealthMonitor.
        """
        for provider in [self.primary, self.fallback]:
            if not health_monitor.is_provider_healthy(provider.name):
                logger.warning(
                    f"[Router] Skipping {provider.name} — marked unhealthy"
                )
                continue

            start = time.time()
            try:
                fn = getattr(provider, method)
                result = await fn(ticker, **kwargs)
                latency = (time.time() - start) * 1000
                health_monitor.record_success(provider.name, latency)
                logger.info(
                    f"[Router] {method}({ticker}) ← {provider.name} "
                    f"in {latency:.0f}ms"
                )
                return result
            except Exception as e:
                latency = (time.time() - start) * 1000
                error_type = (
                    "rate_limit" if "429" in str(e) or "rate limit" in str(e).lower()
                    else "timeout" if "timeout" in str(e).lower()
                    else "unknown"
                )
                health_monitor.record_failure(provider.name, error_type)
                logger.warning(
                    f"[Router] {provider.name} failed for "
                    f"{method}({ticker}): {e}"
                )

        raise RuntimeError(
            f"All providers failed for {method}({ticker})"
        )

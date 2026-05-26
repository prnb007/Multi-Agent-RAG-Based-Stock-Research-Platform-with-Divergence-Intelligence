import time
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ProviderStats:
    total_calls: int = 0
    total_failures: int = 0
    rate_limit_hits: int = 0
    timeout_hits: int = 0
    recent_latencies: deque = field(default_factory=lambda: deque(maxlen=50))
    last_failure_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return (self.total_calls - self.total_failures) / self.total_calls

    @property
    def avg_latency_ms(self) -> float:
        if not self.recent_latencies:
            return 0.0
        return sum(self.recent_latencies) / len(self.recent_latencies)

    @property
    def is_healthy(self) -> bool:
        # Unhealthy if: >3 consecutive failures OR success rate <50%
        return self.consecutive_failures < 3 and self.success_rate >= 0.5


class ProviderHealthMonitor:
    """
    Tracks per-provider health metrics.
    ProviderRouter uses this to decide which provider to prefer.
    """

    def __init__(self):
        self._stats: dict[str, ProviderStats] = defaultdict(ProviderStats)

    def record_success(self, provider: str, latency_ms: float) -> None:
        stats = self._stats[provider]
        stats.total_calls += 1
        stats.consecutive_failures = 0
        stats.last_success_at = datetime.utcnow()
        stats.recent_latencies.append(latency_ms)
        logger.debug(f"[Health] {provider} success in {latency_ms:.0f}ms")

    def record_failure(self, provider: str, error_type: str) -> None:
        stats = self._stats[provider]
        stats.total_calls += 1
        stats.total_failures += 1
        stats.consecutive_failures += 1
        stats.last_failure_at = datetime.utcnow()

        if error_type == "rate_limit":
            stats.rate_limit_hits += 1
        elif error_type == "timeout":
            stats.timeout_hits += 1

        logger.warning(
            f"[Health] {provider} failure ({error_type}) — "
            f"consecutive: {stats.consecutive_failures}, "
            f"success rate: {stats.success_rate:.0%}"
        )

    def is_provider_healthy(self, provider: str) -> bool:
        return self._stats[provider].is_healthy

    def get_healthiest_provider(self, providers: list[str]) -> str:
        """Return the provider with best health score from the list."""
        def score(p: str) -> float:
            s = self._stats[p]
            # Higher is better: success rate weighted against latency
            latency_penalty = min(s.avg_latency_ms / 5000, 0.5)
            return s.success_rate - latency_penalty

        return max(providers, key=score)

    def get_all_stats(self) -> dict:
        return {
            provider: {
                "total_calls": s.total_calls,
                "success_rate": f"{s.success_rate:.0%}",
                "avg_latency_ms": round(s.avg_latency_ms, 1),
                "consecutive_failures": s.consecutive_failures,
                "rate_limit_hits": s.rate_limit_hits,
                "is_healthy": s.is_healthy,
                "last_success": s.last_success_at.isoformat() if s.last_success_at else None,
                "last_failure": s.last_failure_at.isoformat() if s.last_failure_at else None,
            }
            for provider, s in self._stats.items()
        }

# Global singleton
health_monitor = ProviderHealthMonitor()

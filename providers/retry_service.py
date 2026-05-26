import logging
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    before_sleep_log,
    RetryError,
)
from functools import wraps

logger = logging.getLogger(__name__)

def is_retryable_error(exc: Exception) -> bool:
    """Define which exceptions should trigger a retry."""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        # Retry on 429 (rate limit) and 5xx (server errors)
        return exc.response.status_code in (429, 500, 502, 503, 504)
    if isinstance(exc, httpx.ConnectError):
        return True
    if isinstance(exc, ValueError) and "empty" in str(exc).lower():
        return True
    return False

# Standard retry decorator for provider API calls
# 3 attempts, 2s → 4s → 8s backoff, logs each retry
standard_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception(is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Aggressive retry for critical data (price history)
aggressive_retry = retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=3, max=15),
    retry=retry_if_exception(is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Light retry for non-critical data (news)
light_retry = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception(is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

"""Simple per-FunctionID query rate limiter.

Yuanta's API restricts query/account calls to roughly 3 per second and 600 per
minute.  This limiter uses sliding windows per FunctionID so a single function
cannot exceed either bound.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding-window limiter keyed by function ID."""

    def __init__(
        self,
        max_per_second: int | None = None,
        max_per_minute: int | None = None,
        per_second: int | None = None,
        per_minute: int | None = None,
    ) -> None:
        self.max_per_second = (
            max_per_second if max_per_second is not None else (per_second if per_second is not None else 3)
        )
        self.max_per_minute = (
            max_per_minute if max_per_minute is not None else (per_minute if per_minute is not None else 600)
        )
        self._lock = threading.Lock()
        self._second: dict[str, deque[float]] = defaultdict(deque)
        self._minute: dict[str, deque[float]] = defaultdict(deque)

    def acquire(self, function_id: str) -> bool:
        """Record a call for ``function_id`` if within both rate limits.

        Returns ``True`` when the call is allowed, ``False`` when rate limited.
        """
        now = time.monotonic()
        with self._lock:
            second_window = self._second[function_id]
            minute_window = self._minute[function_id]

            while second_window and second_window[0] <= now - 1.0:
                second_window.popleft()
            while minute_window and minute_window[0] <= now - 60.0:
                minute_window.popleft()

            if self.max_per_second >= 0 and len(second_window) >= self.max_per_second:
                return False
            if self.max_per_minute >= 0 and len(minute_window) >= self.max_per_minute:
                return False

            second_window.append(now)
            minute_window.append(now)
            return True

    # Convenience alias matching common rate-limiter APIs.
    allow = acquire
    check = acquire


__all__ = ["RateLimiter"]

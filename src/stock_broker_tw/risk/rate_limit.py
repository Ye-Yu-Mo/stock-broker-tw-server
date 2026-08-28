"""Unified per-FunctionID and per-account rate limiter.

Yuanta's API restricts calls per FunctionID and account.  This limiter uses
sliding windows keyed by ``(function_id, key)`` so a single function cannot
exceed either the second or minute bound for a given account/dimension.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

_LIMIT_SPEC = tuple[int | None, int | None]


class RateLimiter:
    """Sliding-window limiter keyed by function ID and optional account key."""

    def __init__(
        self,
        max_per_second: int | None = None,
        max_per_minute: int | None = None,
        per_second: int | None = None,
        per_minute: int | None = None,
        limits: dict[str, _LIMIT_SPEC] | None = None,
    ) -> None:
        self.max_per_second = (
            max_per_second if max_per_second is not None else (per_second if per_second is not None else 3)
        )
        self.max_per_minute = (
            max_per_minute if max_per_minute is not None else (per_minute if per_minute is not None else 600)
        )
        self._limits = dict(limits or {})
        self._lock = threading.Lock()
        self._second: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._minute: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._rejected: dict[str, int] = defaultdict(int)
        self._allowed: dict[str, int] = defaultdict(int)

    def set_limit(self, function_id: str, max_per_second: int | None, max_per_minute: int | None) -> None:
        """Set/override limits for one FunctionID."""
        with self._lock:
            self._limits[function_id] = (max_per_second, max_per_minute)

    def _limit_for(self, function_id: str) -> tuple[int | None, int | None]:
        override = self._limits.get(function_id)
        if override is not None:
            return override
        return self.max_per_second, self.max_per_minute

    def acquire(self, function_id: str, key: str | None = None, account: str | None = None) -> bool:
        """Record a call for ``function_id``/``key`` if within limits.

        ``key`` is the per-account dimension; ``account`` is accepted as an
        alias.  Returns ``True`` when the call is allowed, ``False`` when rate
        limited.
        """
        now = time.monotonic()
        key = key or account
        window_key = (function_id, key or "")
        max_second, max_minute = self._limit_for(function_id)
        with self._lock:
            second_window = self._second[window_key]
            minute_window = self._minute[window_key]

            while second_window and second_window[0] <= now - 1.0:
                second_window.popleft()
            while minute_window and minute_window[0] <= now - 60.0:
                minute_window.popleft()

            if max_second is not None and max_second >= 0 and len(second_window) >= max_second:
                self._rejected[function_id] += 1
                return False
            if max_minute is not None and max_minute >= 0 and len(minute_window) >= max_minute:
                self._rejected[function_id] += 1
                return False

            second_window.append(now)
            minute_window.append(now)
            self._allowed[function_id] += 1
            return True

    def rejected_count(self, function_id: str | None = None) -> int:
        """Return the number of rejected calls for a FunctionID (or all)."""
        with self._lock:
            if function_id is None:
                return sum(self._rejected.values())
            return self._rejected.get(function_id, 0)

    def allowed_count(self, function_id: str | None = None) -> int:
        """Return the number of allowed calls for a FunctionID (or all)."""
        with self._lock:
            if function_id is None:
                return sum(self._allowed.values())
            return self._allowed.get(function_id, 0)

    # Convenience aliases matching common rate-limiter APIs.
    allow = acquire
    check = acquire


__all__ = ["RateLimiter"]

"""Automatic circuit breaker for Yuanta adapter calls.

The breaker protects trading endpoints from sending requests while the broker
adapter is repeatedly failing or timing out.  Read-only/quote calls are not
gated by the breaker, but write operations are rejected with 503 while it is
open.
"""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from stock_broker_tw.metrics import metrics


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


class CircuitBreaker:
    """A small thread-safe consecutive-failure breaker with auto-recovery."""

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        name: str = "yuanta",
        notifier: Any = None,
    ) -> None:
        self.name = name
        self.failure_threshold = max(1, int(failure_threshold))
        self.cooldown_seconds = max(0.0, float(cooldown_seconds))
        self.notifier = notifier
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._last_failure: float | None = None
        self._last_error: str | None = None
        self._rejections = 0
        metrics.circuit_breaker_state.labels(name=self.name).set(0)

    # -- state -------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    @property
    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    @property
    def last_error(self) -> str | None:
        with self._lock:
            return self._last_error

    @property
    def last_failure_at(self) -> str | None:
        with self._lock:
            if self._last_failure is None:
                return None
            return datetime.fromtimestamp(self._last_failure, tz=UTC).isoformat()

    @property
    def consecutive_failures(self) -> int:
        with self._lock:
            return self._consecutive_failures

    @property
    def rejections(self) -> int:
        with self._lock:
            return self._rejections

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "is_open": self.is_open,
            "consecutive_failures": self.consecutive_failures,
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "last_error": self.last_error,
            "last_failure_at": self.last_failure_at,
            "rejections": self.rejections,
        }

    # -- operations --------------------------------------------------------

    def allow_request(self) -> bool:
        """Return ``True`` if a write call may proceed.

        While open, calls are rejected until the cooldown elapses; the first
        request after cooldown is allowed as a half-open probe.
        """
        with self._lock:
            if self._state != CircuitState.OPEN:
                return True
            if self._opened_at is not None and time.monotonic() - self._opened_at >= self.cooldown_seconds:
                self._state = CircuitState.HALF_OPEN
                return True
            self._rejections += 1
            metrics.circuit_breaker_rejections_total.labels(name=self.name).inc()
            return False

    def record_success(self) -> None:
        """Record a successful call and close the breaker if half/open."""
        with self._lock:
            was_open = self._state in {CircuitState.OPEN, CircuitState.HALF_OPEN}
            self._consecutive_failures = 0
            if self._state in {CircuitState.OPEN, CircuitState.HALF_OPEN}:
                self._state = CircuitState.CLOSED
                self._opened_at = None
                self._last_error = None
            if was_open:
                metrics.circuit_breaker_state.labels(name=self.name).set(0)
                self._notify("circuit.closed", "熔断恢复", {"name": self.name, "state": self._state.value})

    def record_failure(self, error: Any = None) -> None:
        """Record a failed call; open after the consecutive threshold."""
        with self._lock:
            self._consecutive_failures += 1
            self._last_failure = time.monotonic()
            self._last_error = str(error) if error is not None else f"failure #{self._consecutive_failures}"
            if self._consecutive_failures >= self.failure_threshold:
                was_open = self._state == CircuitState.OPEN
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                metrics.circuit_breaker_state.labels(name=self.name).set(1)
                if not was_open:
                    metrics.circuit_breaker_opens_total.labels(name=self.name).inc()
                    self._notify(
                        "circuit.opened",
                        "自动熔断开启",
                        {
                            "name": self.name,
                            "threshold": self.failure_threshold,
                            "error": self._last_error,
                        },
                    )

    def manual_reset(self) -> None:
        """Close the breaker immediately (used by resume/ops)."""
        with self._lock:
            was_open = self._state != CircuitState.CLOSED
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = None
            self._last_error = None
            metrics.circuit_breaker_state.labels(name=self.name).set(0)
            if was_open:
                self._notify("circuit.closed", "熔断恢复", {"name": self.name, "state": self._state.value})

    def _notify(self, event: str, title: str, fields: dict[str, Any]) -> None:
        if self.notifier is None:
            return
        try:
            method = getattr(self.notifier, "send", None)
            if callable(method):
                method(event, title, fields)
        except Exception:
            # Notification failures must never affect breaker state.
            pass


__all__ = ["CircuitBreaker", "CircuitState"]

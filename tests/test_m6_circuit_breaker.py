"""M6 circuit breaker and manual panic tests."""

from __future__ import annotations

import threading
import time

from stock_broker_tw.risk.circuit_breaker import CircuitBreaker, CircuitState


def test_circuit_breaker_opens_after_consecutive_failures() -> None:
    breaker = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    assert breaker.allow_request() is True
    breaker.record_failure("boom 1")
    breaker.record_failure("boom 2")
    assert breaker.allow_request() is True
    breaker.record_failure("boom 3")
    assert breaker.state == CircuitState.OPEN
    assert breaker.allow_request() is False
    assert "boom 3" in (breaker.last_error or "")


def test_circuit_breaker_recovers_after_cooldown() -> None:
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=0.01)
    breaker.record_failure("fail")
    breaker.record_failure("fail")
    assert breaker.state == CircuitState.OPEN
    time.sleep(0.02)
    assert breaker.allow_request() is True
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request() is True


def test_circuit_breaker_is_thread_safe() -> None:
    breaker = CircuitBreaker(failure_threshold=5, cooldown_seconds=60)
    errors: list[Exception] = []

    def worker() -> None:
        try:
            for _ in range(100):
                breaker.record_failure("x")
                breaker.allow_request()
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors

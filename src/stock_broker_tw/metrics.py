"""Prometheus metrics for the broker HTTP service."""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


class Metrics:
    """Container for process-wide Prometheus metric objects."""

    def __init__(self) -> None:
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests handled by the service",
            ["method", "path", "status"],
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "path"],
        )
        self.login_attempts_total = Counter(
            "login_attempts_total",
            "Total Yuanta login attempts",
            ["result"],
        )
        self.logout_attempts_total = Counter(
            "logout_attempts_total",
            "Total Yuanta logout attempts",
            ["result"],
        )
        self.event_queue_size = Gauge(
            "event_queue_size",
            "Current number of events waiting in the OnResponse queue",
        )
        self.ws_connections = Gauge(
            "ws_connections",
            "Current number of connected WebSocket clients",
        )
        self.risk_rejections_total = Counter(
            "risk_rejections_total",
            "Total requests rejected by risk/security checks",
            ["reason"],
        )
        self.rate_limited_total = Counter(
            "rate_limited_total",
            "Total requests rejected by the unified rate limiter",
            ["function"],
        )
        self.circuit_breaker_state = Gauge(
            "circuit_breaker_state",
            "Current circuit breaker state (1 = open, 0 = closed/half-open)",
            ["name"],
        )
        self.circuit_breaker_opens_total = Counter(
            "circuit_breaker_opens_total",
            "Total times the circuit breaker has opened",
            ["name"],
        )
        self.circuit_breaker_rejections_total = Counter(
            "circuit_breaker_rejections_total",
            "Total write requests rejected while the circuit is open",
            ["name"],
        )


metrics = Metrics()


def render_metrics() -> bytes:
    """Return Prometheus text format for all default registry metrics."""
    return generate_latest()


__all__ = [
    "CONTENT_TYPE_LATEST",
    "Metrics",
    "metrics",
    "render_metrics",
]

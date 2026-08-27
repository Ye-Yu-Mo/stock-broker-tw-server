"""Tests for Prometheus metrics output."""

from __future__ import annotations

from stock_broker_tw.metrics import metrics, render_metrics


def test_render_metrics_contains_core_metrics() -> None:
    text = render_metrics().decode()
    assert "http_requests_total" in text
    assert "login_attempts_total" in text
    assert "logout_attempts_total" in text
    assert "event_queue_size" in text
    assert "ws_connections" in text


def test_metrics_object_exposes_counters() -> None:
    metrics.login_attempts_total.labels(result="success").inc()
    text = render_metrics().decode()
    assert 'login_attempts_total{result="success"}' in text

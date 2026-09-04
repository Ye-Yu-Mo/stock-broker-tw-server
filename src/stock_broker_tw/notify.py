"""Webhook notifications for key broker events.

Currently supports generic JSON webhooks plus Feishu/DingTalk/WeCom payload
shapes.  Sending is best-effort and never raises so notifications do not affect
the main trading flow.

Alert messages can be configured per event in ``[notify.events]``:

.. code-block:: toml

    [notify]
    enabled = true
    webhook_url = "https://example.com/hook"
    webhook_type = "feishu"

    [notify.events]
    "order.status" = { enabled = true, title = "订单状态变化", template = "[订单] {client_order_id} -> {status}" }
"""

from __future__ import annotations

import json
import logging
import urllib.request
from datetime import UTC, datetime
from typing import Any

from stock_broker_tw.metrics import metrics

logger = logging.getLogger(__name__)


class _SafeFormatDict(dict):
    """dict that renders missing template keys as empty strings."""

    def __missing__(self, key: str) -> str:
        return ""


def format_message(event: str, title: str, fields: dict[str, Any]) -> str:
    """Build a readable text message for a notification event."""
    lines = [f"[{title}]"]
    if event:
        lines.append(f"event: {event}")
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def format_template(template: str, event: str, title: str, fields: dict[str, Any]) -> str:
    """Render a configurable message template.

    Available placeholders include ``{event}``, ``{title}`` and any field name
    from ``fields``.  Missing fields render as empty strings.
    """
    values = _SafeFormatDict({"event": event, "title": title, **fields})
    return template.format_map(values)


def build_payload(
    event: str,
    title: str,
    fields: dict[str, Any],
    webhook_type: str = "generic",
    text: str | None = None,
) -> dict[str, Any]:
    """Build a webhook payload for the configured provider."""
    text = text or format_message(event, title, fields)
    normalized = (webhook_type or "generic").lower()
    if normalized in {"feishu", "lark"}:
        return {"msg_type": "text", "content": {"text": text}}
    if normalized in {"dingtalk", "dingding"}:
        return {"msgtype": "text", "text": {"content": text}}
    if normalized in {"wecom", "weixin", "wechat", "enterprise_wechat"}:
        return {"msgtype": "text", "text": {"content": text}}
    return {"event": event, "title": title, "text": text, "fields": fields}


class Notifier:
    """Best-effort webhook notifier with per-event message configuration."""

    def __init__(
        self,
        enabled: bool = True,
        webhook_url: str = "",
        webhook_type: str = "generic",
        secret: str | None = None,
        timeout: float = 3.0,
        config: Any = None,
        events: dict[str, Any] | None = None,
    ) -> None:
        self.events: dict[str, Any] = dict(events or {})
        self.secret = secret
        if config is not None:
            enabled = bool(getattr(config, "enabled", enabled))
            webhook_url = getattr(config, "webhook_url", webhook_url) or ""
            webhook_type = getattr(config, "webhook_type", webhook_type) or webhook_type
            secret = getattr(config, "secret", None) or secret
            timeout = float(getattr(config, "timeout", timeout))
            configured_events = getattr(config, "events", None)
            if configured_events:
                self.events.update(configured_events)
        self.enabled = bool(enabled and webhook_url)
        self.webhook_url = webhook_url
        self.webhook_type = webhook_type or "generic"
        self.secret = secret or None
        self.timeout = timeout

    @staticmethod
    def _record_sent(event: str) -> None:
        metrics.notifications_sent_total.labels(event=event).inc()

    @staticmethod
    def _record_failed(event: str) -> None:
        metrics.notifications_failed_total.labels(event=event).inc()

    @staticmethod
    def _severity_for(event: str, fields: dict[str, Any]) -> Any:
        """Map broker events to lark_alert card severity levels."""
        from lark_alert import Severity

        status = str(fields.get("status") or "").upper()
        if event in {"risk.rejected", "order.broker_error", "circuit.opened", "recovery.error"}:
            return Severity.Error
        if event == "risk.panic" or status in {"REJECTED", "FAILED", "CANCELLED"}:
            return Severity.Warning
        if event == "circuit.closed" or status == "FILLED":
            return Severity.Success
        return Severity.Info

    def _resolve(self, event: str, title: str, fields: dict[str, Any]) -> tuple[str, str]:
        """Return ``(title, text)`` after applying per-event configuration."""
        cfg = self.events.get(event)
        if cfg is None:
            return title, format_message(event, title, fields)

        enabled = getattr(cfg, "enabled", True)
        if not enabled:
            return title, ""

        resolved_title = getattr(cfg, "title", None) or title
        template = getattr(cfg, "template", None)
        if template:
            return resolved_title, format_template(template, event, resolved_title, fields)
        return resolved_title, format_message(event, resolved_title, fields)

    def send(self, event: str, title: str, fields: dict[str, Any] | None = None) -> bool:
        """Send a notification synchronously. Returns ``True`` on success."""
        if not self.enabled or not self.webhook_url:
            return False
        fields = fields or {}
        resolved_title, text = self._resolve(event, title, fields)
        if not text:
            # Event is explicitly disabled in configuration.
            return False

        if self.webhook_type.lower() in {"feishu", "lark"}:
            try:
                from lark_alert import Card, LarkAlert
            except Exception:  # noqa: BLE001 - optional dependency fallback
                logger.debug("lark_alert is not installed; falling back to built-in webhook sender")
            else:
                try:
                    alert = LarkAlert(
                        self.webhook_url,
                        secret=self.secret,
                        timeout_secs=int(self.timeout),
                        max_retries=1,
                    )
                    summary = event
                    if fields.get("client_order_id"):
                        summary = f"{event} · {fields['client_order_id']}"
                    card = (
                        Card(
                            service="stock-broker-tw-server",
                            node=str(fields.get("node") or "local"),
                            timestamp=datetime.now(UTC).isoformat(),
                            content=text,
                        )
                        .severity(self._severity_for(event, fields))
                        .title(resolved_title)
                        .summary(summary)
                        .environment(str(fields.get("environment") or "unknown"))
                    )
                    for key, value in fields.items():
                        card.field(str(key), str(value))
                    alert.send_card(card)
                    self._record_sent(event)
                    return True
                except Exception as exc:  # noqa: BLE001 - notification must be best-effort
                    logger.warning("notify lark_alert card failed: %s", exc)
                    self._record_failed(event)
                    return False

        payload = build_payload(event, resolved_title, fields, self.webhook_type, text=text)
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            # A 2xx is enough; urllib raises HTTPError for non-2xx responses.
            with urllib.request.urlopen(request, timeout=self.timeout):  # noqa: S310
                pass
            self._record_sent(event)
            return True
        except Exception as exc:  # noqa: BLE001 - notification must be best-effort
            logger.warning("notify webhook failed: %s", exc)
            self._record_failed(event)
            return False

    async def asend(self, event: str, title: str, fields: dict[str, Any] | None = None) -> bool:
        """Async wrapper around :meth:`send` (runs in a thread)."""
        import asyncio

        return await asyncio.to_thread(self.send, event, title, fields)


__all__ = ["Notifier", "build_payload", "format_message", "format_template"]

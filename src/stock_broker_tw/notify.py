"""Webhook notifications for key broker events.

Currently supports generic JSON webhooks plus Feishu/DingTalk/WeCom payload
shapes.  Sending is best-effort and never raises so notifications do not affect
the main trading flow.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


def format_message(event: str, title: str, fields: dict[str, Any]) -> str:
    """Build a readable text message for a notification event."""
    lines = [f"[{title}]"]
    if event:
        lines.append(f"event: {event}")
    for key, value in fields.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def build_payload(
    event: str,
    title: str,
    fields: dict[str, Any],
    webhook_type: str = "generic",
) -> dict[str, Any]:
    """Build a webhook payload for the configured provider."""
    text = format_message(event, title, fields)
    normalized = (webhook_type or "generic").lower()
    if normalized in {"feishu", "lark"}:
        return {"msg_type": "text", "content": {"text": text}}
    if normalized in {"dingtalk", "dingding"}:
        return {"msgtype": "text", "text": {"content": text}}
    if normalized in {"wecom", "weixin", "wechat", "enterprise_wechat"}:
        return {"msgtype": "text", "text": {"content": text}}
    return {"event": event, "title": title, "text": text, "fields": fields}


class Notifier:
    """Best-effort webhook notifier."""

    def __init__(
        self,
        enabled: bool = True,
        webhook_url: str = "",
        webhook_type: str = "generic",
        timeout: float = 3.0,
        config: Any = None,
    ) -> None:
        if config is not None:
            enabled = bool(getattr(config, "enabled", enabled))
            webhook_url = getattr(config, "webhook_url", webhook_url) or ""
            webhook_type = getattr(config, "webhook_type", webhook_type) or webhook_type
            timeout = float(getattr(config, "timeout", timeout))
        self.enabled = bool(enabled and webhook_url)
        self.webhook_url = webhook_url
        self.webhook_type = webhook_type or "generic"
        self.timeout = timeout

    def send(self, event: str, title: str, fields: dict[str, Any] | None = None) -> bool:
        """Send a notification synchronously. Returns ``True`` on success."""
        if not self.enabled or not self.webhook_url:
            return False
        payload = build_payload(event, title, fields or {}, self.webhook_type)
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
            return True
        except Exception as exc:  # noqa: BLE001 - notification must be best-effort
            logger.warning("notify webhook failed: %s", exc)
            return False

    async def asend(self, event: str, title: str, fields: dict[str, Any] | None = None) -> bool:
        """Async wrapper around :meth:`send` (runs in a thread)."""
        import asyncio

        return await asyncio.to_thread(self.send, event, title, fields)


__all__ = ["Notifier", "build_payload", "format_message"]

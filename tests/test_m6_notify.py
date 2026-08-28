"""M6 notification module tests."""

from __future__ import annotations

import json
from unittest import mock

from stock_broker_tw.notify import Notifier, format_message


def test_format_message_contains_title_and_fields() -> None:
    text = format_message("order.updated", "订单状态变化", {"client_order_id": "C001", "status": "FILLED"})
    assert "订单状态变化" in text
    assert "C001" in text
    assert "FILLED" in text


def test_notifier_disabled_without_webhook() -> None:
    notifier = Notifier(enabled=True, webhook_url="")
    assert notifier.enabled is False
    assert notifier.send("order.updated", "title", {"a": 1}) is False


def test_notifier_posts_webhook_payload() -> None:
    notifier = Notifier(enabled=True, webhook_url="http://example.test/hook", webhook_type="feishu")
    with mock.patch("urllib.request.urlopen") as mocked:
        assert notifier.send("risk.rejected", "风控拒绝", {"reason": "BLACKLISTED"}) is True
    assert mocked.call_count == 1
    request = mocked.call_args[0][0]
    body = json.loads(request.data.decode())
    assert body["msg_type"] == "text"
    assert "风控拒绝" in body["content"]["text"]


def test_notifier_unreachable_webhook_does_not_raise() -> None:
    notifier = Notifier(enabled=True, webhook_url="http://example.test/hook", timeout=0.01)
    with mock.patch("urllib.request.urlopen", side_effect=RuntimeError("network down")):
        assert notifier.send("order.updated", "title", {}) is False

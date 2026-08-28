"""M6 end-to-end: login -> order -> report -> WebSocket push -> status update."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from stock_broker_tw.config import AccountConfig, ServerConfig, Settings, StateConfig
from stock_broker_tw.main import create_app
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent


class FakeE2EAdapter:
    def __init__(self) -> None:
        self.event_queue = EventQueue()
        self.opened = False
        self.logged_in = False
        self.disposed = False
        self.last_login_result = None
        self.calls: list[str] = []
        self.sent_orders: list[dict] = []

    def open(self) -> None:
        self.opened = True
        self.calls.append("open")

    def reset_login_result(self) -> None:
        self.last_login_result = None

    def login(self, account: str, password: str, pfx_path=None, pfx_pass=None) -> bool:
        self.logged_in = True
        self.calls.append("login")
        self.last_login_result = {
            "login_list": [
                {"account": account, "name": "測試", "investor_id": "A123456789"}
            ]
        }
        self.event_queue.put(YuantaEvent(1, 0, "Login", None, None))
        return True

    def logout(self) -> bool:
        self.logged_in = False
        self.calls.append("logout")
        return True

    def send_stock_order(self, account: str, order: dict, timeout: float = 10.0):
        self.sent_orders.append({"account": account, "order": order})
        return {
            "result_count": {"msg_code": "0001", "msg_content": "ok", "count": 1},
            "result_list": [
                {
                    "identify": order.get("identify", 1),
                    "reply_code": 0,
                    "order_no": "H00001",
                    "trade_date": "2026/08/28",
                    "err_type": "",
                    "err_no": "",
                    "advisory": "",
                }
            ],
        }


def test_full_trading_loop(tmp_path: Path) -> None:
    adapter = FakeE2EAdapter()
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
        state=StateConfig(db_path=str(tmp_path / "state.db")),
    )
    app = create_app(settings=settings, adapter=adapter)
    headers = {"Authorization": "Bearer test-token"}

    with TestClient(app) as client:
        login = client.post("/api/v1/session/login", json={}, headers=headers)
        assert login.status_code == 200
        assert adapter.logged_in is True

        order = client.post(
            "/api/v1/orders/stock",
            json={
                "client_order_id": "C001",
                "action": "new",
                "stk_code": "2330",
                "side": "B",
                "price": 500.0,
                "quantity": 10,
                "account": "S98875005091",
            },
            headers=headers,
        )
        assert order.status_code == 200, order.text
        assert order.json()["data"]["order_no"] == "H00001"
        assert order.json()["data"]["status"] == "ACCEPTED"

        with client.websocket_connect("/ws?token=test-token") as ws:
            welcome = ws.receive_json()
            assert welcome["type"] == "welcome"

            adapter.event_queue.put(
                YuantaEvent(
                    2,
                    0,
                    "RR_RealReport",
                    None,
                    {
                        "basket_no": "C001",
                        "order_no": "H00001",
                        "order_qty": 10,
                        "ok_qty": 10,
                        "order_status": 8,
                        "last_order_status": 8,
                        "price": 500.0,
                        "trade_date": "2026/08/28",
                        "company_no": "2330",
                        "bs": "B",
                    },
                )
            )
            raw = ws.receive_json()
            # It may be the raw event first or the processed report.
            if raw["type"] == "RR_RealReport":
                raw = ws.receive_json()
            assert raw["type"] in {"real_report", "order.updated"}

            stored = client.app.state.store.get_stock_order("C001")
            assert stored is not None
            assert stored["status"] == "FILLED"

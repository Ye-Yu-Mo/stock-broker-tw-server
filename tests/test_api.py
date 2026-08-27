"""Integration tests for FastAPI routes with a fake Yuanta adapter."""

from __future__ import annotations

from typing import ClassVar

from fastapi.testclient import TestClient

from stock_broker_tw.config import AccountConfig, ServerConfig, Settings
from stock_broker_tw.main import create_app
from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent


class FakeStatus:
    MsgCode = "0001"
    MsgContent = "成功"
    Count = 1


class FakeLoginData:
    Account = "S98875005091"
    Name = "測試用戶"
    InvestorID = "A123456789"
    SellerNo = "9527"


class FakeLoginResult:
    LoginStatus = FakeStatus()
    LoginList: ClassVar[list[FakeLoginData]] = [FakeLoginData()]


class FakeAdapter:
    def __init__(self) -> None:
        self.event_queue = EventQueue()
        self.opened = False
        self.logged_in = False
        self.disposed = False
        self.last_login_result = None
        self.logout_called = False

    def open(self) -> None:
        self.opened = True

    def reset_login_result(self) -> None:
        self.last_login_result = None

    def login(self, account: str, password: str, pfx_path=None, pfx_pass=None) -> bool:
        from stock_broker_tw.yuanta.serializer import login_result_to_dict

        self.logged_in = True
        self.last_login_result = login_result_to_dict(FakeLoginResult())
        self.event_queue.put(YuantaEvent(1, 0, "Login", None, FakeLoginResult()))
        return True

    def logout(self) -> bool:
        self.logout_called = True
        self.logged_in = False
        return True


def make_client() -> TestClient:
    settings = Settings(
        server=ServerConfig(api_token="test-token"),
        account=AccountConfig(account="S98875005091", password="1234"),
    )
    app = create_app(settings=settings, adapter=FakeAdapter())
    return TestClient(app)


def auth(token: str = "test-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_is_public_and_returns_status() -> None:
    with make_client() as client:
        res = client.get("/health")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] in {"ok", "degraded"}
        assert "adapter_ready" in body
        assert "login_status" in body
        assert "event_queue_size" in body


def test_metrics_is_public_and_returns_prometheus_text() -> None:
    with make_client() as client:
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]
        assert b"login_attempts_total" in res.content


def test_status_requires_token() -> None:
    with make_client() as client:
        res = client.get("/api/v1/session/status")
        assert res.status_code == 401


def test_status_with_token() -> None:
    with make_client() as client:
        res = client.get("/api/v1/session/status", headers=auth())
        assert res.status_code == 200
        assert res.json()["data"]["opened"] is False


def test_login_success_via_api() -> None:
    with make_client() as client:
        res = client.post("/api/v1/session/login", json={}, headers=auth())
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["code"] == 0
        assert body["data"]["login"]["login_list"][0]["account"] == "S98875005091"


def test_logout_via_api() -> None:
    with make_client() as client:
        res = client.post("/api/v1/session/logout", headers=auth())
        assert res.status_code == 200, res.text


def test_metrics_endpoint_is_also_available_via_api() -> None:
    with make_client() as client:
        res = client.get("/api/v1/session/status", headers=auth())
        assert res.status_code == 200

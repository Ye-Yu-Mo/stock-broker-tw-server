"""Tests for M2 pydantic-settings based configuration loading."""

from __future__ import annotations

from pathlib import Path

from stock_broker_tw.config import load_settings


def test_load_settings_reads_toml(tmp_path: Path) -> None:
    cfg = tmp_path / "test.toml"
    cfg.write_text(
        """
[server]
host = "0.0.0.0"
port = 9000
api_token = "toml-token"
log_level = "DEBUG"
log_json = false

[yuanta]
environment = "PROD"
spark_api_dir = "/opt/yuanta"
login_timeout = 7.5

[account]
account = "S98875005091"
password = "1234"

[audit]
enabled = false
file = "/tmp/audit.log"
""",
        encoding="utf-8",
    )
    settings = load_settings(cfg)
    assert settings.server.host == "0.0.0.0"
    assert settings.server.port == 9000
    assert settings.server.api_token == "toml-token"
    assert settings.server.log_level == "DEBUG"
    assert settings.server.log_json is False
    assert settings.yuanta.environment == "PROD"
    assert settings.yuanta.spark_api_dir == "/opt/yuanta"
    assert settings.yuanta.login_timeout == 7.5
    assert settings.account.account == "S98875005091"
    assert settings.account.password == "1234"
    assert settings.audit.enabled is False
    assert settings.audit.file == "/tmp/audit.log"


def test_env_overrides_toml(monkeypatch, tmp_path: Path) -> None:
    cfg = tmp_path / "test.toml"
    cfg.write_text(
        """
[server]
host = "0.0.0.0"
api_token = "toml-token"

[yuanta]
environment = "UAT"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("YUANTA_SERVER__HOST", "1.2.3.4")
    monkeypatch.setenv("YUANTA_SERVER__API_TOKEN", "env-token")
    monkeypatch.setenv("YUANTA_YUANTA__ENVIRONMENT", "PROD")
    settings = load_settings(cfg)
    assert settings.server.host == "1.2.3.4"
    assert settings.server.api_token == "env-token"
    assert settings.yuanta.environment == "PROD"


def test_load_settings_default_config_exists() -> None:
    settings = load_settings()
    assert settings.server.host == "127.0.0.1"
    assert settings.yuanta.environment == "UAT"
    assert settings.account.account == "S98875005091"


def test_m1_flat_env_variables_are_supported(monkeypatch) -> None:
    """The M1 CLI style YUANTA_* variables must not crash pydantic-settings."""
    monkeypatch.setenv("YUANTA_ACCOUNT", "flat-account")
    monkeypatch.setenv("YUANTA_PASSWORD", "flat-pass")
    monkeypatch.setenv("YUANTA_ENV", "PROD")
    monkeypatch.setenv("YUANTA_SPARK_API_DIR", "/opt/flat")
    settings = load_settings("/tmp/does-not-exist-for-flat-test.toml")
    assert settings.account.account == "flat-account"
    assert settings.account.password == "flat-pass"
    assert settings.yuanta.environment == "PROD"
    assert settings.yuanta.spark_api_dir == "/opt/flat"


from stock_broker_tw.config import (
    QueryConfig,
    QuoteConfig,
    RateLimitConfig,
    Settings,
    resolve_query_rate_limits,
    resolve_quote_rate_limits,
)


def test_resolve_query_rate_limits_prefers_legacy_when_new_is_default(tmp_path: Path) -> None:
    settings = Settings(
        query=QueryConfig(rate_limit_per_second=7, rate_limit_per_minute=700)
    )
    assert resolve_query_rate_limits(settings) == (7, 700)


def test_resolve_query_rate_limits_new_unified_wins(tmp_path: Path) -> None:
    settings = Settings(
        rate_limit=RateLimitConfig(query_per_second=9, query_per_minute=900),
        query=QueryConfig(rate_limit_per_second=7, rate_limit_per_minute=700),
    )
    assert resolve_query_rate_limits(settings) == (9, 900)


def test_resolve_quote_rate_limits_prefers_legacy_when_new_is_default(tmp_path: Path) -> None:
    settings = Settings(quote=QuoteConfig(rate_limit_per_second=8))
    assert resolve_quote_rate_limits(settings) == (8, None)


def test_resolve_quote_rate_limits_new_unified_wins(tmp_path: Path) -> None:
    settings = Settings(
        rate_limit=RateLimitConfig(quote_per_second=12, quote_per_minute=1200),
        quote=QuoteConfig(rate_limit_per_second=8),
    )
    assert resolve_quote_rate_limits(settings) == (12, 1200)

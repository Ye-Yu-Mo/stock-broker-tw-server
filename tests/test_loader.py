"""Unit tests for Yuanta loader path resolution without loading native DLLs."""

from __future__ import annotations

from stock_broker_tw.yuanta.loader import (
    _detect_dotnet_root,
    get_default_spark_api_dir,
    get_environment_mode,
)


def test_default_spark_api_dir_points_to_vendor(monkeypatch) -> None:
    monkeypatch.delenv("YUANTA_SPARK_API_DIR", raising=False)
    path = get_default_spark_api_dir()
    assert path.name == "sparkapi"
    assert path.parent.name == "yuanta"
    assert path.parent.parent.name == "vendor"


def test_environment_mode_returns_string_when_assembly_not_loaded() -> None:
    # When YuantaOneAPI is not importable (no pythonnet bootstrap yet), the
    # loader intentionally returns the original string so callers can fall back.
    mode = get_environment_mode("UAT")
    assert mode == "UAT"


def test_detect_dotnet_root_uses_explicit_env(monkeypatch) -> None:
    monkeypatch.setenv("DOTNET_ROOT", "/custom/dotnet")
    assert _detect_dotnet_root() == "/custom/dotnet"


def test_detect_dotnet_root_parses_dotnet_info(monkeypatch) -> None:
    monkeypatch.delenv("DOTNET_ROOT", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/dotnet" if name == "dotnet" else None)

    class FakeProc:
        stdout = """
.NET SDK:
 Version: 8.0.100

Environment variables:
  DOTNET_ROOT   [/opt/dotnet/root]
"""
        stderr = ""

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: FakeProc())
    assert _detect_dotnet_root() == "/opt/dotnet/root"


def test_detect_dotnet_root_returns_none_without_dotnet(monkeypatch) -> None:
    monkeypatch.delenv("DOTNET_ROOT", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert _detect_dotnet_root() is None

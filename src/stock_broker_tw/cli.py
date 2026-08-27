"""Command line entry point for Milestone 1 login verification.

Runs the minimal Yuanta lifecycle::

    Open -> Login -> wait for Login OnResponse -> LogOut -> Close -> Dispose

The script supports both Windows-style account/password login and
macOS/Linux-style Pfx credential login.
"""

from __future__ import annotations

import argparse
import os
import queue
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

from stock_broker_tw.yuanta.adapter import YuantaAdapter
from stock_broker_tw.yuanta.serializer import login_result_to_dict


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load a TOML config file. Missing files are treated as empty config."""
    path = Path(config_path or os.environ.get("YUANTA_CONFIG", "config/default.toml"))
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="yuanta_check",
        description="Verify Yuanta Open/Login/LogOut/Close lifecycle",
    )
    parser.add_argument("--config", default=os.environ.get("YUANTA_CONFIG", "config/default.toml"))
    parser.add_argument("--account", default=os.environ.get("YUANTA_ACCOUNT"))
    parser.add_argument("--password", default=os.environ.get("YUANTA_PASSWORD"))
    parser.add_argument("--pfx-path", default=os.environ.get("YUANTA_PFX_PATH"))
    parser.add_argument("--pfx-pass", default=os.environ.get("YUANTA_PFX_PASS"))
    parser.add_argument(
        "--env",
        dest="environment",
        default=os.environ.get("YUANTA_ENV", "UAT"),
    )
    parser.add_argument("--spark-api-dir", default=os.environ.get("YUANTA_SPARK_API_DIR"))
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("YUANTA_LOGIN_TIMEOUT", "15")),
    )
    return parser.parse_args(argv)


def build_login_config(args: argparse.Namespace) -> dict[str, Any]:
    """Merge CLI arguments, environment variables, and TOML config."""
    file_cfg = load_config(getattr(args, "config", None))
    account_cfg = file_cfg.get("account", {})
    yuanta_cfg = file_cfg.get("yuanta", {})

    timeout = getattr(args, "timeout", None)
    if timeout is None:
        timeout = yuanta_cfg.get("login_timeout", 15)

    return {
        "account": getattr(args, "account", None) or account_cfg.get("account"),
        "password": getattr(args, "password", None) or account_cfg.get("password"),
        "pfx_path": getattr(args, "pfx_path", None) or account_cfg.get("pfx_path"),
        "pfx_pass": getattr(args, "pfx_pass", None) or account_cfg.get("pfx_pass"),
        "environment": getattr(args, "environment", None) or yuanta_cfg.get("environment", "UAT"),
        "spark_api_dir": getattr(args, "spark_api_dir", None) or yuanta_cfg.get("spark_api_dir"),
        "timeout": float(timeout),
    }


def wait_for_login_response(event_queue: Any, timeout: float = 15.0) -> dict[str, Any]:
    """Block until a ``Login`` OnResponse event arrives and serialize it."""
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"timed out after {timeout:.1f}s waiting for Login response")
        try:
            event = event_queue.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError(
                f"timed out after {timeout:.1f}s waiting for Login response"
            ) from exc
        if event.str_index == "Login":
            return login_result_to_dict(event.obj_value)


def execute_lifecycle(
    adapter: Any,
    account: str,
    password: str,
    pfx_path: str | None = None,
    pfx_pass: str | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """Run Open -> Login -> wait -> LogOut -> Close -> Dispose.

    Returns the serialized ``LoginResult`` dict.  Cleanup always runs.
    """
    adapter.open()
    try:
        accepted = adapter.login(
            account,
            password,
            pfx_path=pfx_path,
            pfx_pass=pfx_pass,
        )
        if not accepted:
            raise RuntimeError("Yuanta Login call was rejected (returned False)")
        result = wait_for_login_response(adapter.event_queue, timeout=timeout)
        login_list = result.get("login_list") or []
        print(f"Login response: {result}")
        for item in login_list:
            print(
                f"  account={item.get('account')} "
                f"name={item.get('name')} "
                f"investor_id={item.get('investor_id')}"
            )
        return result
    finally:
        try:
            adapter.logout()
        except Exception as exc:  # noqa: BLE001 - cleanup must continue
            print(f"logout warning: {exc}", file=sys.stderr)
        adapter.close()
        adapter.dispose()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = build_login_config(args)

    if not cfg.get("account") or not cfg.get("password"):
        print(
            "account and password are required. "
            "Use --account/--password or config/default.toml.",
            file=sys.stderr,
        )
        return 2

    adapter = YuantaAdapter(
        environment=cfg["environment"],
        spark_api_dir=cfg.get("spark_api_dir"),
    )
    try:
        execute_lifecycle(
            adapter,
            account=cfg["account"],
            password=cfg["password"],
            pfx_path=cfg.get("pfx_path"),
            pfx_pass=cfg.get("pfx_pass"),
            timeout=cfg["timeout"],
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should print and exit cleanly
        print(f"yuanta_check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

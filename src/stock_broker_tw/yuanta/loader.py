"""Load pythonnet and the Yuanta Spark API .NET assembly.

The loader keeps all .NET bootstrap details in one place:

1. Select the ``coreclr`` runtime via ``pythonnet.load``.
2. Add the vendor directory containing ``YuantaSparkAPI.dll``.
3. ``clr.AddReference("YuantaSparkAPI")`` so ``from YuantaOneAPI import ...``
   works.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

_loaded = False
_lock = threading.Lock()


def _detect_dotnet_root() -> str | None:
    """Return a usable ``DOTNET_ROOT`` when pythonnet cannot find one itself.

    On Homebrew-installed .NET (common on macOS), ``dotnet --info`` prints the
    effective DOTNET_ROOT even when the environment variable is not exported.
    pythonnet/coreclr needs this value to bootstrap the runtime.
    """
    explicit = os.environ.get("DOTNET_ROOT")
    if explicit:
        return explicit

    dotnet = shutil.which("dotnet")
    if dotnet is None:
        return None

    try:
        proc = subprocess.run(
            [dotnet, "--info"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None

    match = re.search(r"DOTNET_ROOT\s+\[(.*?)\]", proc.stdout)
    if match:
        return match.group(1).strip() or None

    # Fallback for Homebrew-style layouts: /opt/homebrew/opt/dotnet -> libexec
    candidate = Path(dotnet).resolve()
    for parent in candidate.parents:
        if parent.name in {"bin", "sdk"}:
            root = parent.parent
            if (root / "shared" / "Microsoft.NETCore.App").exists():
                return str(root)
    return None


def get_default_spark_api_dir() -> Path:
    """Return the conventional vendor directory for the Yuanta DLLs."""
    env_dir = os.environ.get("YUANTA_SPARK_API_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "vendor" / "yuanta" / "sparkapi"


def ensure_loaded(spark_api_dir: str | Path | None = None) -> None:
    """Load the .NET runtime and add the YuantaSparkAPI reference.

    This function is idempotent and thread-safe.
    """
    global _loaded
    if _loaded:
        return
    with _lock:
        if _loaded:
            return

        # pythonnet must be configured before clr is imported.  On macOS the
        # Homebrew dotnet often does not export DOTNET_ROOT, so we help it.
        dotnet_root = _detect_dotnet_root()
        if dotnet_root:
            os.environ.setdefault("DOTNET_ROOT", dotnet_root)

        from pythonnet import load

        load("coreclr")

        import clr

        dll_dir = Path(spark_api_dir or get_default_spark_api_dir()).expanduser().resolve()
        if not dll_dir.exists():
            raise FileNotFoundError(
                f"Yuanta Spark API directory not found: {dll_dir}. "
                "Set YUANTA_SPARK_API_DIR or pass spark_api_dir."
            )

        if sys.platform == "win32":
            os.add_dll_directory(str(dll_dir))
        sys.path.append(str(dll_dir))

        clr.AddReference("YuantaSparkAPI")
        _loaded = True


def load_runtime(spark_api_dir: str | Path | None = None) -> None:
    """Alias for :func:`ensure_loaded`."""
    ensure_loaded(spark_api_dir)


# Common aliases used in different codebases.
load_yuanta = ensure_loaded
load_assembly = ensure_loaded
setup = ensure_loaded


def get_environment_mode(environment: str) -> Any:
    """Map ``"UAT"``/``"PROD"`` to the Yuanta enum value.

    If the Yuanta assembly is not loaded yet, returns the input string so tests
    and callers can still use a light-weight mode placeholder.
    """
    try:
        from YuantaOneAPI import enumEnvironmentMode
    except Exception:
        return environment

    modes = {
        "UAT": enumEnvironmentMode.UAT,
        "PROD": enumEnvironmentMode.PROD,
    }
    return modes.get(str(environment).upper(), environment)


def create_trader(
    environment: str = "UAT",
    log_type: str = "COMMON",
    pmm_server_check: bool = False,
    spark_api_dir: str | Path | None = None,
) -> Any:
    """Load the assembly and create a configured ``YuantaSparkAPITrader``."""
    ensure_loaded(spark_api_dir)

    from YuantaOneAPI import YuantaSparkAPITrader, enumLogType

    trader = YuantaSparkAPITrader()

    log_type_map = {
        "COMMON": getattr(enumLogType, "COMMON", None),
        "NONE": getattr(enumLogType, "NONE", None),
        "DEBUG": getattr(enumLogType, "DEBUG", None),
        "ERROR": getattr(enumLogType, "ERROR", None),
    }
    if log_type_map.get(log_type.upper()) is not None:
        trader.SetLogType(log_type_map[log_type.upper()])
    trader.SetPMMServerCheck(bool(pmm_server_check))
    return trader

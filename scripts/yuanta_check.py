#!/usr/bin/env python
"""M1 login verification script.

Usage::

    uv run python scripts/yuanta_check.py --account S98875005091 --password 1234
    uv run python scripts/yuanta_check.py --pfx-path /path/cert.pfx --pfx-pass yuanta ...
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running directly from a source checkout without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stock_broker_tw.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

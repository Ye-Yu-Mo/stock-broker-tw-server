"""Allow ``python -m stock_broker_tw`` to run the M1 CLI."""

from stock_broker_tw.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

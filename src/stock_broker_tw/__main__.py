"""Allow ``python -m stock_broker_tw`` to start the FastAPI service."""

from stock_broker_tw.main import run

if __name__ == "__main__":
    run()

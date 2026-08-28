"""M4 feature 2: per-account serial order queue."""

from __future__ import annotations

import asyncio

from stock_broker_tw.engine.queue import SerialOrderQueue


def run(coro):
    return asyncio.run(coro)


def test_same_account_operations_are_serialized() -> None:
    events: list[str] = []

    async def main() -> None:
        queue = SerialOrderQueue()

        async def op(name: str):
            events.append(f"{name}:start")
            await asyncio.sleep(0.02)
            events.append(f"{name}:end")

        await asyncio.gather(
            queue.submit("A", lambda: op("first")),
            queue.submit("A", lambda: op("second")),
        )

    run(main())
    assert events == ["first:start", "first:end", "second:start", "second:end"]


def test_different_accounts_can_run_concurrently() -> None:
    events: list[str] = []

    async def main() -> None:
        queue = SerialOrderQueue()

        async def op(name: str):
            events.append(f"{name}:start")
            await asyncio.sleep(0.02)
            events.append(f"{name}:end")

        await asyncio.gather(
            queue.submit("A", lambda: op("a")),
            queue.submit("B", lambda: op("b")),
        )

    run(main())
    assert set(events) == {"a:start", "b:start", "a:end", "b:end"}


def test_submit_returns_task_result_and_propagates_errors() -> None:
    async def main() -> None:
        queue = SerialOrderQueue()
        assert await queue.submit("A", lambda: 42) == 42
        try:
            await queue.submit("A", lambda: (_ for _ in ()).throw(ValueError("boom")))
        except ValueError as exc:
            assert str(exc) == "boom"
        else:
            raise AssertionError("expected ValueError")

    run(main())

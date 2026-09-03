"""Unit tests for the thread-safe OnResponse event queue."""

from __future__ import annotations

import asyncio
import queue
import threading

import pytest

from stock_broker_tw.yuanta.events import EventQueue, YuantaEvent


def make_event(value: str) -> YuantaEvent:
    return YuantaEvent(
        int_mark=1,
        dw_index=0,
        str_index=value,
        obj_handle=None,
        obj_value=value,
    )


def test_event_queue_put_get_preserves_order() -> None:
    eq = EventQueue()
    eq.put(make_event("Login"))
    eq.put(make_event("LogOut"))
    assert eq.get(timeout=0.1).str_index == "Login"
    assert eq.get(timeout=0.1).str_index == "LogOut"


def test_event_queue_get_timeout_raises_empty() -> None:
    eq = EventQueue()
    with pytest.raises(queue.Empty):
        eq.get(timeout=0.05)


def test_event_queue_get_nowait() -> None:
    eq = EventQueue()
    eq.put(make_event("Login"))
    assert eq.get_nowait().str_index == "Login"
    with pytest.raises(queue.Empty):
        eq.get_nowait()


def test_event_queue_qsize() -> None:
    eq = EventQueue()
    eq.put(make_event("a"))
    eq.put(make_event("b"))
    assert eq.qsize() == 2


def test_event_queue_is_thread_safe() -> None:
    eq = EventQueue()
    make_event("sentinel")

    def producer(start: threading.Event) -> None:
        start.wait()
        for i in range(50):
            eq.put(make_event(f"e{i}"))

    start = threading.Event()
    threads = [threading.Thread(target=producer, args=(start,)) for _ in range(4)]
    for t in threads:
        t.start()
    start.set()
    for t in threads:
        t.join()

    seen = [eq.get(timeout=0.5).str_index for _ in range(200)]
    assert len(seen) == 200
    assert seen.count("e0") == 4
    assert seen.count("e49") == 4


def test_event_queue_async_get() -> None:
    async def scenario() -> None:
        eq = EventQueue()

        async def delayed_put() -> None:
            await asyncio.sleep(0.02)
            eq.put(make_event("async-login"))

        task = asyncio.create_task(delayed_put())
        event = await eq.async_get(timeout=0.5)
        await task
        assert event.str_index == "async-login"

    asyncio.run(scenario())


def test_event_queue_async_get_does_not_lose_events_put_before_start() -> None:
    async def scenario() -> None:
        eq = EventQueue()
        eq.put(make_event("before-async"))
        event = await eq.async_get(timeout=0.5)
        assert event.str_index == "before-async"

    asyncio.run(scenario())


def test_async_event_consumer_dispatches_until_stop() -> None:
    async def scenario() -> None:
        eq = EventQueue()
        received: list[YuantaEvent] = []
        consumer = eq.consume(received.append)
        await consumer.start()
        eq.put(make_event("one"))
        await asyncio.sleep(0.01)
        eq.put(make_event("two"))
        await asyncio.sleep(0.01)
        await consumer.stop()
        assert [e.str_index for e in received] == ["one", "two"]

    asyncio.run(scenario())


def test_async_owner_does_not_leave_sync_backlog() -> None:
    async def scenario() -> None:
        eq = EventQueue()
        eq.put(make_event("before-owner"))
        received: list[YuantaEvent] = []
        consumer = eq.consume(received.append)
        await consumer.start()
        for name in ("one", "two"):
            eq.put(make_event(name))
        await asyncio.sleep(0.02)
        await consumer.stop()

        assert [event.str_index for event in received] == ["before-owner", "one", "two"]
        assert eq.qsize() == 0

    asyncio.run(scenario())


def test_async_owner_stop_does_not_poison_sync_queue() -> None:
    async def scenario() -> None:
        eq = EventQueue()
        consumer = eq.consume(lambda event: None)
        await consumer.start()
        await consumer.stop()
        assert eq.qsize() == 0
        with pytest.raises(queue.Empty):
            eq.get_nowait()

    asyncio.run(scenario())

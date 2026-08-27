"""Thread-safe OnResponse event queue and asyncio bridge.

The Yuanta .NET callback may fire on a non-Python / background thread.  The
adapter writes raw events into :class:`EventQueue`; the rest of the application
can consume them either synchronously (``get``) or from asyncio (``async_get``
and :class:`AsyncEventConsumer`).
"""

from __future__ import annotations

import asyncio
import queue
import threading
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from stock_broker_tw.metrics import metrics

T = TypeVar("T")

_SENTINEL = object()


@dataclass(frozen=True)
class YuantaEvent:
    """A raw ``OnResponse`` event.

    The field names mirror the .NET delegate signature:
    ``OnResponseEventHandler(intMark, dwIndex, strIndex, objHandle, objValue)``.
    """

    int_mark: int
    dw_index: int
    str_index: str
    obj_handle: Any
    obj_value: Any

    @property
    def intMark(self) -> int:
        return self.int_mark

    @property
    def dwIndex(self) -> int:
        return self.dw_index

    @property
    def strIndex(self) -> str:
        return self.str_index

    @property
    def objHandle(self) -> Any:
        return self.obj_handle

    @property
    def objValue(self) -> Any:
        return self.obj_value


class EventQueue:
    """A small thread-safe queue for ``OnResponse`` events.

    The queue is dual-backed: a regular :class:`queue.Queue` for synchronous
    consumers and an :class:`asyncio.Queue` for async consumers.  Writes from
    any thread are safe in both modes.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[YuantaEvent | object] = queue.Queue()
        self._async_queue: asyncio.Queue[YuantaEvent | object] | None = None
        self._async_loop: asyncio.AbstractEventLoop | None = None
        self._async_queue_lock = threading.Lock()

    def put(self, event: YuantaEvent) -> None:
        """Put an event into the queue. Safe to call from any thread."""
        self._queue.put(event)
        metrics.event_queue_size.set(self.qsize())
        async_queue = self._async_queue
        if async_queue is not None and self._async_loop is not None:
            self._async_loop.call_soon_threadsafe(async_queue.put_nowait, event)

    def put_nowait(self, event: YuantaEvent) -> None:
        """Compatibility alias matching :class:`queue.Queue`."""
        self.put(event)

    def put_event(self, event: YuantaEvent) -> None:
        """Alias for :meth:`put`."""
        self.put(event)

    def get(self, timeout: float | None = None) -> YuantaEvent:
        """Remove and return the next event.

        Raises :class:`queue.Empty` when the timeout expires.
        """
        item = self._queue.get(timeout=timeout)
        if item is _SENTINEL:
            raise queue.Empty
        metrics.event_queue_size.set(self.qsize())
        return item  # type: ignore[return-value]

    def get_nowait(self) -> YuantaEvent:
        """Remove and return an event without blocking."""
        item = self._queue.get_nowait()
        if item is _SENTINEL:
            raise queue.Empty
        metrics.event_queue_size.set(self.qsize())
        return item  # type: ignore[return-value]

    def get_event(self, timeout: float | None = None) -> YuantaEvent:
        """Alias for :meth:`get`."""
        return self.get(timeout)

    def qsize(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

    def _ensure_async_queue(self) -> asyncio.Queue[YuantaEvent | object]:
        if self._async_queue is None:
            # asyncio.Queue must be created from a running event loop.
            loop = asyncio.get_running_loop()
            with self._async_queue_lock:
                if self._async_queue is None:
                    self._async_queue = asyncio.Queue()
                    self._async_loop = loop
                    # If events were put before the first async consumer was
                    # created, move them to the async side so they are not lost.
                    while True:
                        try:
                            item = self._queue.get_nowait()
                        except queue.Empty:
                            break
                        self._async_queue.put_nowait(item)
        return self._async_queue

    async def async_get(self, timeout: float | None = None) -> YuantaEvent:
        """Asynchronously wait for the next event without blocking the loop.

        Internal sentinels are returned to async consumers so they can stop
        cleanly; synchronous :meth:`get` still raises ``queue.Empty`` for them.
        """
        async_queue = self._ensure_async_queue()
        try:
            if timeout is None:
                return await async_queue.get()  # type: ignore[return-value]
            return await asyncio.wait_for(async_queue.get(), timeout)  # type: ignore[return-value]
        except TimeoutError:
            raise queue.Empty from None

    def consume(
        self, handler: Callable[[YuantaEvent], Any]
    ) -> AsyncEventConsumer:
        """Create an async consumer that dispatches events to ``handler``."""
        return AsyncEventConsumer(self, handler)


class AsyncEventConsumer:
    """An asyncio task that continuously consumes an :class:`EventQueue`."""

    def __init__(
        self,
        event_queue: EventQueue,
        handler: Callable[[YuantaEvent], Any],
    ) -> None:
        self._event_queue = event_queue
        self._handler = handler
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start consuming events in the background."""
        if self._task is not None and not self._task.done():
            return
        # Make sure the async queue exists before the producer starts putting
        # events; otherwise events enqueued immediately after start() could be
        # missed by the asyncio side.
        self._event_queue._ensure_async_queue()
        self._task = asyncio.create_task(self._run())

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the consumer after all already-queued events are processed."""
        if self._task is None or self._task.done():
            return
        self._event_queue.put(_SENTINEL)  # type: ignore[arg-type]
        await asyncio.wait_for(asyncio.shield(self._task), timeout=timeout)

    async def _run(self) -> None:
        while True:
            item = await self._event_queue.async_get()
            if item is _SENTINEL:
                break
            result = self._handler(item)
            if isinstance(result, Awaitable):
                await result


# Common aliases.
OnResponseQueue = EventQueue
ResponseEvent = YuantaEvent

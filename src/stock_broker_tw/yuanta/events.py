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
    request_id: str | None = None

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
        self._async_only = False
        self._async_queue_lock = threading.Lock()

    def put(self, event: YuantaEvent) -> None:
        """Put an event into the queue. Safe to call from any thread."""
        with self._async_queue_lock:
            async_queue = self._async_queue
            async_loop = self._async_loop
            if not self._async_only:
                self._queue.put(event)
        metrics.event_queue_size.set(self.qsize())
        if async_queue is not None and async_loop is not None:
            async_loop.call_soon_threadsafe(async_queue.put_nowait, event)

    def put_nowait(self, event: YuantaEvent) -> None:
        """Compatibility alias matching :class:`queue.Queue`."""
        self.put(event)

    def put_event(self, event: YuantaEvent) -> None:
        """Alias for :meth:`put`."""
        self.put(event)

    def _put_async(self, item: YuantaEvent | object) -> None:
        """Put an internal item on the async owner queue only."""
        with self._async_queue_lock:
            async_queue = self._async_queue
            async_loop = self._async_loop
        if async_queue is None or async_loop is None:
            raise RuntimeError("async queue has not been initialized")
        async_loop.call_soon_threadsafe(async_queue.put_nowait, item)

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
        with self._async_queue_lock:
            if self._async_only and self._async_queue is not None:
                return self._async_queue.qsize()
            return self._queue.qsize()

    def empty(self) -> bool:
        return self.qsize() == 0

    def _ensure_async_queue(self) -> asyncio.Queue[YuantaEvent | object]:
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

    def claim_async_owner(self) -> None:
        """Make the current event loop the sole owner of future events."""
        loop = asyncio.get_running_loop()
        with self._async_queue_lock:
            if self._async_loop is not None and self._async_loop is not loop:
                raise RuntimeError("event queue is owned by another event loop")
            if self._async_queue is None:
                self._async_queue = asyncio.Queue()
                self._async_loop = loop
            while True:
                try:
                    item = self._queue.get_nowait()
                except queue.Empty:
                    break
                self._async_queue.put_nowait(item)
            self._async_only = True
        metrics.event_queue_size.set(self.qsize())

    async def async_get(self, timeout: float | None = None) -> YuantaEvent:
        """Asynchronously wait for the next event without blocking the loop."""
        async_queue = self._ensure_async_queue()
        try:
            if timeout is None:
                item = await async_queue.get()
            else:
                item = await asyncio.wait_for(async_queue.get(), timeout)
        except TimeoutError:
            raise queue.Empty from None
        metrics.event_queue_size.set(self.qsize())
        return item  # type: ignore[return-value]

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
        # Claim ownership before the producer can enqueue new events so the
        # synchronous compatibility queue cannot retain an unbounded copy.
        self._event_queue.claim_async_owner()
        self._task = asyncio.create_task(self._run())

    async def stop(self, timeout: float = 5.0) -> None:
        """Stop the consumer after all already-queued events are processed."""
        if self._task is None or self._task.done():
            return
        self._event_queue._put_async(_SENTINEL)
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

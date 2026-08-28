"""M4 per-account serial order queue.

The Yuanta API is event-driven and effectively single-connection.  To avoid
interleaved ``SendStockOrder`` responses, all trading operations for the same
account are serialized through an asyncio lock.  Different accounts may run
concurrently.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class SerialOrderQueue:
    """Serialize order operations per account.

    ``submit`` enqueues a callable and waits for its completion.  Operations
    submitted for the same account are executed one at a time; operations for
    different accounts are not blocked by each other.
    """

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    async def submit(
        self,
        account: str,
        task: Callable[[], Awaitable[Any] | Any],
        operation_id: str | None = None,
    ) -> Any:
        """Run ``task`` after earlier tasks for the same account finish."""
        lock = self._locks.setdefault(account, asyncio.Lock())
        async with lock:
            result = task()
            if isinstance(result, Awaitable):
                result = await result
            return result

    async def enqueue(
        self,
        account: str,
        task: Callable[[], Awaitable[Any] | Any],
        operation_id: str | None = None,
    ) -> Any:
        """Alias for :meth:`submit`."""
        return await self.submit(account, task, operation_id=operation_id)

    def pending(self, account: str | None = None) -> int:
        """Return approximate number of queued/waiting operations.

        The lock implementation does not maintain an explicit queue; the value
        is 0 unless a task is currently waiting on the lock, in which case it
        reflects only the lock's internal waiter count.
        """
        if account is not None:
            lock = self._locks.get(account)
            return len(getattr(lock, "_waiters", ())) if lock is not None else 0
        return sum(self.pending(account) for account in self._locks)


# Common alias.
OrderQueue = SerialOrderQueue

__all__ = ["OrderQueue", "SerialOrderQueue"]

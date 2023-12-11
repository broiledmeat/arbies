import asyncio
from contextlib import asynccontextmanager
from typing import Any


class ContextLock:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._contexts: dict[Any, asyncio.Lock] = {}

    @asynccontextmanager
    async def acquire(self, context: Any):
        await self._lock.acquire()

        if context not in self._contexts:
            self._contexts[context] = asyncio.Lock()
        lock = self._contexts[context]

        self._lock.release()

        try:
            await lock.acquire()
            yield lock
        finally:
            lock.release()

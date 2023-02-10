from __future__ import annotations
from abc import ABC
from arbies.manager import Manager


class Supplier(ABC):
    def __init__(self, manager: Manager):
        self._manager: Manager = manager

    @property
    def manager(self) -> Manager:
        return self._manager

    async def startup(self):
        pass

    async def shutdown(self):
        pass

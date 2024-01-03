from abc import ABC
from arbies.manager import Manager


class Run(ABC):
    name: str | None = None

    def __init__(self, *params: str):
        pass

    async def render(self, manager: Manager):
        raise NotImplemented

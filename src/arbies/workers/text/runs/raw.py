from arbies.manager import Manager
from arbies.workers.text.runs import Run


class Raw(Run):
    name: str | None = None

    def __init__(self, *params: str):
        super().__init__(*params)
        self.text = ''.join(params)

    async def render(self, manager: Manager):
        return self.text

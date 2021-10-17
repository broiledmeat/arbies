from __future__ import annotations
from pathlib import Path
from PIL import Image
from typing import Optional
from arbies import drawing
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker


class NetworkStatusWorker(Worker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.loop_interval = 0.5 * 60
        self.interface: Optional[str] = None

    def render(self):
        image = Image.new('1', self.size, 1)

        icon_name: str = 'wifi-off'
        state_path: Path = Path(f'/sys/class/net/{self.interface}/operstate')

        if state_path.is_file() and state_path.read_bytes() == b'up\n':
            icon_name = 'wifi'

        image.paste(drawing.get_icon(icon_name, tuple(self.size)))

        self.serve(image)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> NetworkStatusWorker:
        # noinspection PyTypeChecker
        worker: NetworkStatusWorker = super().from_config(manager, config)

        worker.interface = config.get('interface', worker.interface)

        return worker

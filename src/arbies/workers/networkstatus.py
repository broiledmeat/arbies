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

        self._interface: Optional[str] = None

    async def _render_internal(self) -> Image.Image:
        image = Image.new('RGBA', self._size)

        icon_name: str = 'wifi-off'
        state_path: Path = Path(f'/sys/class/net/{self._interface}/operstate')

        if state_path.is_file() and state_path.read_bytes() == b'up\n':
            icon_name = 'wifi'

        image.paste(drawing.get_icon(icon_name, tuple(self._size)))

        return image

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> NetworkStatusWorker:
        # noinspection PyTypeChecker
        worker: NetworkStatusWorker = super().from_config(manager, config)

        worker._interface = config.get('Interface', worker._interface)

        return worker

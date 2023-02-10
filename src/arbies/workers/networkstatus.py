from __future__ import annotations
from pathlib import Path
from PIL import Image
from typing import Optional
from arbies import drawing
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker


class NetworkStatusWorker(Worker):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._interface: str = kwargs.get('Interface', '')

    async def _render_internal(self) -> Image.Image:
        image = Image.new('RGBA', self._size)

        icon_name: str = 'wifi-off'
        state_path: Path = Path(f'/sys/class/net/{self._interface}/operstate')

        if state_path.is_file() and state_path.read_bytes() == b'up\n':
            icon_name = 'wifi'

        image.paste(drawing.get_icon(icon_name, tuple(self._size)))

        return image

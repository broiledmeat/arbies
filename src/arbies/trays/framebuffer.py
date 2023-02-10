from __future__ import annotations
from PIL import Image
from arbies.drawing.geometry import Vector2, Box
from arbies.manager import Manager, ConfigDict
from . import Tray
from typing import TYPE_CHECKING, Optional


class FramebufferTray(Tray):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._mode: str = kwargs.get('Mode', 'RGBA')
        path: str = kwargs.get('Path', '/dev/fb0')
        self._path: str = manager.resolve_path(path)


    async def _serve_internal(self, image: Image.Image, updated_boxes: Optional[list[Box]] = None):
        self._manager.log.info(f'Writing to {self._path} {self.size}')
        fb_data = image.tobytes('raw', self._mode)
        with open(self._path, 'wb') as fb:
            fb.write(fb_data)

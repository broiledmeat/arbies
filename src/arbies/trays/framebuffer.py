from __future__ import annotations
from PIL import Image
from arbies.drawing.geometry import Vector2, Box
from arbies.manager import Manager, ConfigDict
from . import Tray
from typing import TYPE_CHECKING, Optional


class FramebufferTray(Tray):
    _default_path = '/dev/fb0'
    _default_format = 'RGBA'

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._path: str = self._default_path
        self._format: str = self._default_format

    async def _serve_internal(self, image: Image.Image, updated_boxes: Optional[list[Box]] = None):
        self._manager.log.info(f'Writing to {self._path} {self.size}')
        fb_data = image.tobytes('raw', self._format)
        with open(self._path, 'wb') as fb:
            fb.write(fb_data)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> FramebufferTray:
        # noinspection PyTypeChecker
        tray: FramebufferTray = super().from_config(manager, config)

        tray._path = config.get('Path', tray._path)
        tray._format = config.get('Format', tray._format)

        return tray

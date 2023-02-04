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

        self.path: str = self._default_path
        self.size: Vector2 = Vector2()
        self.format: str = self._default_format

    async def serve(self, image: Image.Image, updated_boxes: Optional[list[Box]] = None):
        self._manager.log.info(f'Writing to {self.path} {self.size}')

        fb_image = image
        if self.size != image.size:
            fb_image = image.resize(self.size)

        fb_data = fb_image.tobytes('raw', self.format)
        with open(self.path, 'wb') as fb:
            fb.write(fb_data)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> FramebufferTray:
        # noinspection PyTypeChecker
        tray: FramebufferTray = super().from_config(manager, config)

        tray.path = config.get('Path', tray.path)
        tray.size = Vector2(config.get('Size', manager.size))
        tray.format = config.get('Format', tray.format)

        return tray

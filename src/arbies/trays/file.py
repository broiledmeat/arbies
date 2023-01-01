from __future__ import annotations
import os
from PIL import Image
from arbies.manager import Manager, ConfigDict
from . import Tray


class FileTray(Tray):
    _default_format = 'PNG'
    _default_mode = 'RGBA'
    _default_filename = 'output'

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.format: str = self._default_format
        self.mode: str = self._default_mode
        self.path: str = manager.resolve_path(f'{self._default_filename}.{self._default_format.lower()}')

    def serve(self, image: Image.Image):
        target = image if image.mode == self.mode else image.copy().convert(self.mode)
        target.save(self.path, self.format)
        self.manager.log.info(f'Wrote {self.path} ({self.format}, {self.mode})')

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> FileTray:
        # noinspection PyTypeChecker
        tray: FileTray = super().from_config(manager, config)

        tray.format = config.get('Format', tray.format)
        tray.mode = config.get('Mode', tray.mode)
        tray.path = manager.resolve_path(config.get('Path', tray.path))

        return tray

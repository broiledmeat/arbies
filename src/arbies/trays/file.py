from __future__ import annotations
from PIL import Image
from arbies.manager import Manager, ConfigDict
from . import Tray
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from arbies.drawing.geometry import Box


class FileTray(Tray):
    _default_format = 'PNG'
    _default_mode = 'RGBA'
    _default_filename = 'output'

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._format: str = self._default_format
        self._mode: str = self._default_mode
        self._path: str = manager.resolve_path(f'{self._default_filename}.{self._default_format.lower()}')

    async def _serve_internal(self, image: Image.Image, updated_boxes: Optional[list[Box]] = None):
        target = image if image.mode == self._mode else image.copy().convert(self._mode)
        target.save(self._path, self._format)
        self._manager.log.info(f'Wrote {self._path} ({self._format}, {self._mode})')

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> FileTray:
        # noinspection PyTypeChecker
        tray: FileTray = super().from_config(manager, config)

        tray._format = config.get('Format', tray._format)
        tray._mode = config.get('Mode', tray._mode)
        tray._path = manager.resolve_path(config.get('Path', tray._path))

        return tray

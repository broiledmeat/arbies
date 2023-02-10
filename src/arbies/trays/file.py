from __future__ import annotations
from PIL import Image
from arbies.manager import Manager, ConfigDict
from . import Tray
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from arbies.drawing.geometry import Box


class FileTray(Tray):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._format: str = kwargs.get('Format', 'PNG')
        self._mode: str = kwargs.get('Mode', 'RGBA')
        path: str = kwargs.get('Path', f'output.{self._format.lower()}')
        self._path: str = manager.resolve_path(path)

    async def _serve_internal(self, image: Image.Image, updated_boxes: Optional[list[Box]] = None):
        target = image if image.mode == self._mode else image.copy().convert(self._mode)
        target.save(self._path, self._format)
        self._manager.log.info(f'Wrote {self._path} ({self._format}, {self._mode})')

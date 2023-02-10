from __future__ import annotations
from PIL import Image
from arbies.drawing.geometry import Box
from arbies.manager import Manager
from arbies.trays import Tray


class FileTray(Tray):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._format: str = kwargs.get('Format', 'PNG')
        self._mode: str = kwargs.get('Mode', 'RGBA')
        path: str = kwargs.get('Path', f'output.{self._format.lower()}')
        self._path: str = manager.resolve_path(path)

    async def _serve_internal(self, image: Image.Image, updated_boxes: list[Box] | None = None):
        target = image if image.mode == self._mode else image.copy().convert(self._mode)
        target.save(self._path, self._format)
        self._manager.log.info(f'Wrote {self._path} ({self._format}, {self._mode})')

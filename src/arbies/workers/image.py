from __future__ import annotations
from PIL import Image
from typing import Optional
from arbies import drawing
from arbies.drawing import HorizontalAlignment, VerticalAlignment
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker


class ImageWorker(Worker):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        path: str = kwargs.get('Path', '')
        self._path: str = manager.resolve_path(path)

    async def _render_internal(self) -> Image.Image:
        image = Image.new('RGBA', self._size)
        drawing.draw_image(image,
                           Image.open(self._path),
                           resize=True,
                           horizontal_alignment=HorizontalAlignment.CENTER,
                           vertical_alignment=VerticalAlignment.CENTER)
        return image

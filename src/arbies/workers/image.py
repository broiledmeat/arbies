from __future__ import annotations
from PIL import Image
from typing import Optional
from arbies import drawing
from arbies.drawing import HorizontalAlignment, VerticalAlignment
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker


class ImageWorker(Worker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._path: Optional[str] = None

    async def _render_internal(self) -> Image.Image:
        image = Image.new('RGBA', self._size)
        drawing.draw_image(image,
                           Image.open(self._path),
                           resize=True,
                           horizontal_alignment=HorizontalAlignment.CENTER,
                           vertical_alignment=VerticalAlignment.CENTER)
        return image

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> ImageWorker:
        # noinspection PyTypeChecker
        worker: ImageWorker = super().from_config(manager, config)

        worker._path = manager.resolve_path(config.get('Path', worker._path))

        return worker

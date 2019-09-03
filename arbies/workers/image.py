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

        self.loop_interval = 0.5 * 60
        self.path: Optional[str] = None

    def render(self):
        image = Image.new('1', self.size, 1)
        drawing.draw_image(image,
                           Image.open(self.path),
                           resize=True,
                           horizontal_alignment=HorizontalAlignment.CENTER,
                           vertical_alignment=VerticalAlignment.CENTER)
        self.serve(image)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> ImageWorker:
        # noinspection PyTypeChecker
        worker: ImageWorker = super().from_config(manager, config)

        worker.path = config.get('path', worker.path)

        return worker

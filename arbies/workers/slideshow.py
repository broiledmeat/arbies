from __future__ import annotations
import os
import random
from PIL import Image
from typing import Optional, List
from arbies import drawing
from arbies.drawing import HorizontalAlignment, VerticalAlignment
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker


class SlideShowWorker(Worker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.loop_interval = 60
        self.root: Optional[str] = None

        self._image_index = -1
        self._image_paths: Optional[List[str]] = None

    def render(self):
        if self._image_paths is None:
            self._image_paths = self._get_image_paths()
            random.shuffle(self._image_paths)
            self._image_index = 0

        if len(self._image_paths) == 0:
            return

        image = Image.new('1', self.size, 1)
        drawing.draw_image(image,
                           Image.open(self._image_paths[self._image_index]),
                           resize=True,
                           horizontal_alignment=HorizontalAlignment.CENTER,
                           vertical_alignment=VerticalAlignment.CENTER)
        self.serve(image)
        self._image_index = (self._image_index + 1) % len(self._image_paths)

    def _get_image_paths(self) -> List[str]:
        if self.root is None or not os.path.isdir(self.root):
            return []

        return [os.path.join(root, name)
                for root, dirs, files in os.walk(self.root)
                for name in files
                if os.path.splitext(name)[1].lower() in ('.jpg', '.jpeg', '.png')]

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> SlideShowWorker:
        # noinspection PyTypeChecker
        worker: SlideShowWorker = super().from_config(manager, config)

        worker.root = config.get('root', worker.root)

        return worker

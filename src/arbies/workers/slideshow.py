from __future__ import annotations
import os
from PIL import Image, ImageFilter
from typing import Optional
from arbies import drawing
from arbies.drawing import HorizontalAlignment, VerticalAlignment, dithering
from arbies.manager import Manager, ConfigDict
from arbies.suppliers.filesystem import DirectoryIterator, DirectoryIterationMethod, get_dir_iterator
from arbies.workers import Worker


class SlideShowWorker(Worker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.loop_interval: float = 60.0
        self.root: Optional[str] = None

        self._path_iterator: Optional[DirectoryIterator] = None

    def render(self):
        if self._path_iterator is None:
            self._path_iterator = get_dir_iterator(self.root,
                                                   method=DirectoryIterationMethod.Random,
                                                   filter_=r'.*\.(jpg|jpeg|png)$')

        path: str = next(self._path_iterator)

        if not os.path.isfile(path):
            return

        image = Image.new('RGBA', self.size)
        drawing.draw_image(image,
                           Image.open(path),
                           resize=True,
                           horizontal_alignment=HorizontalAlignment.CENTER,
                           vertical_alignment=VerticalAlignment.CENTER)
        self.serve(image)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> SlideShowWorker:
        # noinspection PyTypeChecker
        worker: SlideShowWorker = super().from_config(manager, config)

        worker.root = config.get('root', worker.root)
        worker.loop_interval = config.get('interval', worker.loop_interval)

        return worker

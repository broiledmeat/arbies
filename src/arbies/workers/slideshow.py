from __future__ import annotations
from PIL import Image
from typing import Optional
from arbies import drawing
from arbies.drawing import HorizontalAlignment, VerticalAlignment
from arbies.manager import Manager, ConfigDict
from arbies.suppliers.filesystem import DirectoryIterator, DirectoryIterationMethod, get_dir_iterator
from arbies.workers import LoopIntervalWorker


class SlideShowWorker(LoopIntervalWorker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._root: Optional[str] = None
        self._path_iterator: Optional[DirectoryIterator] = None

    async def _render_internal(self):
        if self._path_iterator is None:
            self._path_iterator = get_dir_iterator(self._root,
                                                   method=DirectoryIterationMethod.Random,
                                                   filter_=r'.*\.(jpg|jpeg|png)$')

        path: str = next(self._path_iterator)
        image = Image.new('RGBA', self._size)
        drawing.draw_image(image,
                           Image.open(path),
                           resize=True,
                           horizontal_alignment=HorizontalAlignment.CENTER,
                           vertical_alignment=VerticalAlignment.CENTER)
        return image

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> SlideShowWorker:
        # noinspection PyTypeChecker
        worker: SlideShowWorker = super().from_config(manager, config)

        worker._root = manager.resolve_path(config.get('Root', worker._root))

        return worker

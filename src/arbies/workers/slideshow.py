from __future__ import annotations
from PIL import Image
from arbies.drawing import HorizontalAlignment, VerticalAlignment, draw_image
from arbies.manager import Manager
from arbies.suppliers.filesystem import DirectoryIterator, DirectoryIterationMethod, get_dir_iterator
from arbies.workers import LoopIntervalWorker


class SlideShowWorker(LoopIntervalWorker):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        path: str = kwargs.get('Root', '')
        self._root: str = manager.resolve_path(path)
        self._path_iterator: DirectoryIterator = get_dir_iterator(self._root,
                                                                  method=DirectoryIterationMethod.Random,
                                                                  filter_=r'.*\.(jpg|jpeg|png)$')

    async def _render_internal(self):
        path: str = next(self._path_iterator)
        image = Image.new('RGBA', self._size)
        draw_image(image,
                   Image.open(path),
                   resize=True,
                   horizontal_alignment=HorizontalAlignment.CENTER,
                   vertical_alignment=VerticalAlignment.CENTER)
        return image

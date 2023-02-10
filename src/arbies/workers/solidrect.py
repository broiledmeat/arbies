from __future__ import annotations
from PIL import Image
from arbies.drawing import ColorType, as_color
from arbies.manager import Manager
from arbies.workers import Worker


class SolidRectWorker(Worker):
    _default_fill: ColorType = (0, 0, 0, 255)

    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._fill: ColorType = as_color(kwargs.get('Fill', self._default_fill))

    async def _render_internal(self):
        return Image.new('RGBA', self._size, self._fill)

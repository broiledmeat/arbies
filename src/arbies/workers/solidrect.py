from __future__ import annotations
from PIL import Image
from arbies.manager import ConfigDict, Manager
from arbies.workers import Worker
from arbies.drawing import as_color
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arbies.drawing import ColorType


class SolidRectWorker(Worker):
    _default_fill: ColorType = 0

    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._fill: ColorType = as_color(kwargs.get('Fill', self._default_fill))

    async def _render_internal(self):
        return Image.new('RGBA', self._size, self._fill)

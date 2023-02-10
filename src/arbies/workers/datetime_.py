from __future__ import annotations
from PIL import Image, ImageDraw
from arbies.drawing import HorizontalAlignment, VerticalAlignment
from arbies.drawing.font import aligned_text
from arbies.manager import Manager
from arbies.suppliers import datetime_ as adt
from arbies.workers import LoopIntervalWorker


class DateTimeWorker(LoopIntervalWorker):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._format: str | None = kwargs.get('Format', None)
        self._horizontal_alignment: HorizontalAlignment = HorizontalAlignment.convert_from(
            kwargs.get('HAlign', HorizontalAlignment.LEFT))
        self._vertical_alignment: VerticalAlignment = VerticalAlignment.convert_from(
            kwargs.get('VAlign', VerticalAlignment.TOP))

    async def _render_internal(self) -> Image.Image:
        now = adt.now_tz()
        text = now.strftime(self._format) if self._format is not None else str(now)

        image = Image.new('RGBA', self._size, 1)
        draw = ImageDraw.Draw(image)

        aligned_text(draw, self._font, text, self.font_fill, self.size,
                     horizontal_alignment=self._horizontal_alignment,
                     vertical_alignment=self._vertical_alignment)

        del draw

        return image

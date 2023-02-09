from __future__ import annotations
from PIL import Image, ImageDraw
from typing import Optional
from arbies.manager import Manager, ConfigDict
from arbies.workers import LoopIntervalWorker
from arbies.suppliers import datetime_ as adt
from arbies import drawing
from arbies.drawing import HorizontalAlignment, VerticalAlignment


class DateTimeWorker(LoopIntervalWorker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._format: Optional[str] = None
        self._horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT
        self._vertical_alignment: VerticalAlignment = VerticalAlignment.TOP

    async def _render_internal(self) -> Image.Image:
        now = adt.now_tz()
        text = now.strftime(self._format) if self._format is not None else str(now)

        self._last_text = text

        image = Image.new('RGBA', self._size, 1)
        draw = ImageDraw.Draw(image)

        drawing.aligned_text(draw, self._font, text, self._font_fill, self._size,
                             horizontal_alignment=self._horizontal_alignment,
                             vertical_alignment=self._vertical_alignment)

        del draw

        return image

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> DateTimeWorker:
        # noinspection PyTypeChecker
        worker: DateTimeWorker = super().from_config(manager, config)

        worker._format = config.get('Format', worker._format)
        worker._horizontal_alignment = HorizontalAlignment.convert_from(
            config.get('HAlign', worker._horizontal_alignment))
        worker._vertical_alignment = VerticalAlignment.convert_from(
            config.get('VAlign', worker._vertical_alignment))

        return worker

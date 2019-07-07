from __future__ import annotations
from PIL import Image, ImageDraw
from typing import Optional
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker
from arbies.suppliers import datetime as adt
from arbies import drawing


class DateTimeWorker(Worker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.loop_interval = 60
        self.format: Optional[str] = None
        self.font_size: int = 16
        self.horizontal_alignment: str = 'left'
        self.vertical_alignment: str = 'top'

        self._last_text = ''

    def render(self):
        now = adt.now_tz()
        text = now.strftime(self.format) if self.format is not None else str(now)

        if text == self._last_text:
            return

        self._last_text = text

        image = Image.new('1', self.size, 1)
        draw = ImageDraw.Draw(image)

        font = drawing.get_font(size=self.font_size)

        drawing.aligned_text(draw, text, self.size,
                             horizontal_alignment=self.horizontal_alignment,
                             vertical_alignment=self.vertical_alignment,
                             font=font)

        del draw
        self.serve(image)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> DateTimeWorker:
        # noinspection PyTypeChecker
        worker: DateTimeWorker = super().from_config(manager, config)

        worker.format = config.get('format', worker.format)
        worker.font_size = config.get('font_size', worker.font_size)
        worker.horizontal_alignment = config.get('horizontal_alignment', worker.horizontal_alignment)
        worker.vertical_alignment = config.get('vertical_alignment', worker.vertical_alignment)

        return worker

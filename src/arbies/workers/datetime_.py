from __future__ import annotations
from PIL import Image, ImageDraw
from arbies.drawing import HorizontalAlignment, VerticalAlignment
from arbies.drawing.font import aligned_text
from arbies.manager import Manager
from arbies.suppliers.datetime_ import DateTimeSupplier
from arbies.suppliers.location import LocationSupplier, Location
from arbies.workers import LoopIntervalWorker
from typing import Callable


# noinspection PyUnusedLocal
async def _render_datetime(worker: DateTimeWorker,
                           draw: ImageDraw.Draw,
                           supplier: DateTimeSupplier,
                           location: Location | None):
    aligned_text(draw, worker.font, supplier.now_tz().strftime(worker.format), worker.font_fill, worker.size,
                 horizontal_alignment=HorizontalAlignment.CENTER,
                 vertical_alignment=VerticalAlignment.CENTER)


async def _render_sunrise(worker: DateTimeWorker,
                          draw: ImageDraw.Draw,
                          supplier: DateTimeSupplier,
                          location: Location | None):
    sun_info = await supplier.get_sun_position_info(supplier.now_tz(), location.coords)
    aligned_text(draw, worker.font, sun_info.sunrise.strftime(worker.format), worker.font_fill, worker.size,
                 horizontal_alignment=HorizontalAlignment.CENTER,
                 vertical_alignment=VerticalAlignment.CENTER)


async def _render_sunset(worker: DateTimeWorker,
                         draw: ImageDraw.Draw,
                         supplier: DateTimeSupplier,
                         location: Location | None):
    sun_info = await supplier.get_sun_position_info(supplier.now_tz(), location.coords)
    aligned_text(draw, worker.font, sun_info.sunset.strftime(worker.format), worker.font_fill, worker.size,
                 horizontal_alignment=HorizontalAlignment.CENTER,
                 vertical_alignment=VerticalAlignment.CENTER)


class DateTimeWorker(LoopIntervalWorker):
    _default_style: str = 'DateTime'
    _styles: dict[str, tuple[Callable, str]] = {
        'DateTime': (_render_datetime, '*/1 * * * *'),
        'SunRise': (_render_sunrise, '0 * * * *'),
        'SunSet': (_render_sunset, '0 * * * *'),
    }

    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._format: str | None = kwargs.get('Format', '%H:%M')
        self._horizontal_alignment: HorizontalAlignment = HorizontalAlignment.convert_from(
            kwargs.get('HAlign', HorizontalAlignment.LEFT))
        self._vertical_alignment: VerticalAlignment = VerticalAlignment.convert_from(
            kwargs.get('VAlign', VerticalAlignment.TOP))

        self._location_name: str | None = kwargs.get('Location', None)
        self._location: Location | None = None

        style_name = kwargs.get('Style', DateTimeWorker._default_style)
        style_func, style_interval = DateTimeWorker._styles[style_name]

        self._render_func: Callable = style_func
        if 'Interval' not in kwargs:
            self._cron_interval = style_interval

    @property
    def format(self) -> str:
        return self._format

    async def _render_internal(self) -> Image.Image:
        if self._location is None:
            location_supplier: LocationSupplier = await self.manager.get_supplier(LocationSupplier)
            self._location = location_supplier.get(self._location_name)

        supplier: DateTimeSupplier = await self.manager.get_supplier(DateTimeSupplier)
        image = Image.new('RGBA', self._size)
        draw = ImageDraw.Draw(image)

        await self._render_func(self, draw, supplier, self._location)

        del draw
        return image

from __future__ import annotations
from PIL import Image, ImageDraw
from arbies.drawing import HorizontalAlignment, VerticalAlignment, get_icon
from arbies.drawing.font import aligned_text, aligned_wrapped_text, get_line_height, get_text_size
from arbies.manager import Manager
from arbies.suppliers.location import LocationSupplier, Location
from arbies.suppliers.weather import WeatherSupplier, WeatherPeriod
from arbies.workers import LoopIntervalWorker
from typing import Callable


async def _render_temperature(worker: WeatherWorker, draw: ImageDraw.Draw, period: WeatherPeriod):
    aligned_text(draw, worker.font, f'{period.temperature}f', worker.font_fill, worker.size,
                 horizontal_alignment=HorizontalAlignment.CENTER,
                 vertical_alignment=VerticalAlignment.CENTER)


async def _render_wind(worker: WeatherWorker, draw: ImageDraw.Draw, period: WeatherPeriod):
    text = f'{period.wind_speed}mph'

    if period.wind_speed == 0:
        aligned_text(draw, worker.font, text, worker.font_fill, worker.size,
                     horizontal_alignment=HorizontalAlignment.CENTER,
                     vertical_alignment=VerticalAlignment.CENTER)
        return

    text_size = get_text_size(worker.font, text)
    icon_size = (get_line_height(worker.font),) * 2

    icon_name = '-'.join(['arrow'] + [WeatherWorker._wind_direction_icon_map[token] for token in period.wind_direction])
    icon = get_icon(icon_name, icon_size)

    x_offset = int((worker.size.x - (icon.width + text_size[0])) / 2)

    draw.bitmap((x_offset, int((worker.size.y / 2) - (icon.height / 2))), icon)

    aligned_text(draw, worker.font, text, worker.font_fill, worker.size,
                 offset=(x_offset + icon.width, 0),
                 vertical_alignment=VerticalAlignment.CENTER)


async def _render_forecast(worker: WeatherWorker, draw: ImageDraw.Draw, period: WeatherPeriod):
    aligned_wrapped_text(draw, worker.font, period.short_forecast, worker.font_fill, worker.size,
                         horizontal_alignment=HorizontalAlignment.CENTER)


async def _render_long_forecast(worker: WeatherWorker, draw: ImageDraw.Draw, period: WeatherPeriod):
    aligned_wrapped_text(draw, worker.font, period.long_forecast, worker.font_fill, worker.size,
                         horizontal_alignment=HorizontalAlignment.CENTER)


class WeatherWorker(LoopIntervalWorker):
    _default_style: str = 'Temperature'
    _styles = {
        'Temperature': (_render_temperature, '0,30 * * * *'),
        'Wind': (_render_wind, '0,30 * * * *'),
        'Forecast': (_render_forecast, '0 * * * *'),
        'LongForecast': (_render_long_forecast, '0 0,12 * * *'),
    }
    _wind_direction_icon_map = {
        'N': 'up',
        'S': 'down',
        'E': 'right',
        'W': 'left'
    }

    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._location_name: str | None = kwargs.get('Location', None)
        self._location: Location | None = None

        style_name = kwargs.get('Style', WeatherWorker._default_style)
        style_func, style_interval = WeatherWorker._styles[style_name]

        self._render_func: Callable = style_func
        if 'Interval' not in kwargs:
            self._cron_interval = style_interval

    async def _render_internal(self) -> Image.Image:
        if self._location is None:
            location_supplier: LocationSupplier = await self.manager.get_supplier(LocationSupplier)
            self._location = location_supplier.get(self._location_name)

        weather_supplier: WeatherSupplier = await self.manager.get_supplier(WeatherSupplier)
        period = await weather_supplier.get_current(self._location.coords)

        image = Image.new('RGBA', self._size)
        draw = ImageDraw.Draw(image)

        await self._render_func(self, draw, period)

        del draw
        return image

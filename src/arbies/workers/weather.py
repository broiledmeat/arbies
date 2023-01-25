from __future__ import annotations
from PIL import Image, ImageDraw
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker
from arbies.suppliers import weather
from arbies.drawing import HorizontalAlignment, VerticalAlignment, get_line_height
from arbies import drawing


class WeatherWorker(Worker):
    _wind_direction_icon_map = {
        'N': 'up',
        'S': 'down',
        'E': 'right',
        'W': 'left'
    }

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._style = 'temperature'
        self._grid: weather.GpsCoords = weather.GpsCoords(42.865, -73.771)  # Albany

    async def _render_internal(self) -> Image.Image:
        image = Image.new('RGBA', self._size)
        draw = ImageDraw.Draw(image)
        period = weather.get_current_period(self._grid)

        if self._style == 'Temperature':
            await self._render_temperature(image, draw, period)
        elif self._style == 'Wind':
            await self._render_wind(image, draw, period)
        elif self._style == 'Forecast':
            await self._render_forecast(image, draw, period)
        elif self._style == 'LongForecast':
            await self._render_long_forecast(image, draw, period)
        else:
            raise ValueError(self._style)

        del draw

        return image

    async def _render_temperature(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_text(draw, self._font, f'{period.temperature}f', self._font_fill, self._size,
                             horizontal_alignment=HorizontalAlignment.CENTER,
                             vertical_alignment=VerticalAlignment.CENTER)

    async def _render_wind(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        text = f'{period.wind_speed}mph'

        if period.wind_speed == 0:
            drawing.aligned_text(draw, self._font, text, self._font_fill, self._size,
                                 horizontal_alignment=HorizontalAlignment.CENTER,
                                 vertical_alignment=VerticalAlignment.CENTER)
            return

        text_size = draw.textsize(text, font=self._font)
        icon_size = (get_line_height(self._font), ) * 2

        icon_name = '-'.join(['arrow'] + [self._wind_direction_icon_map[token] for token in period.wind_direction])
        icon = drawing.get_icon(icon_name, icon_size)

        x_offset = int((self._size[0] - (icon.width + text_size[0])) / 2)

        image.paste(icon, (x_offset, int((self._size[1] / 2) - (icon.height / 2))))

        drawing.aligned_text(draw, self._font, text, self._font_fill, self._size,
                             offset=(x_offset + icon.width, 0),
                             vertical_alignment=VerticalAlignment.CENTER)

    async def _render_forecast(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_wrapped_text(draw, self._font, period.short_forecast, self._font_fill, self._size,
                                     horizontal_alignment=HorizontalAlignment.CENTER)

    async def _render_long_forecast(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_wrapped_text(draw, self._font, period.long_forecast, self._font_fill, self._size,
                                     horizontal_alignment=HorizontalAlignment.CENTER)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> WeatherWorker:
        weather.init_from_config(manager.config)

        # noinspection PyTypeChecker
        worker: WeatherWorker = super().from_config(manager, config)

        worker._style = config.get('Style', worker._style)

        if 'Location' in config:
            worker._location = weather.get_location_coords(config['Location'])
        elif 'Locations' in manager.config and len(manager.config['Locations']) >= 1:
            first_location = list(manager.config['Locations'].keys())[0]
            worker._location = weather.get_location_coords(first_location)

        return worker

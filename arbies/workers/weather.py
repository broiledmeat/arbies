from __future__ import annotations
from PIL import Image, ImageDraw
from typing import Tuple
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker
from arbies.suppliers import weather
from arbies.drawing import get_line_height
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

        self.position = (0, 100)
        self.loop_interval = 30 * 60

        self.type = 'temperature'
        self.office: str = 'ALY'
        self.grid: Tuple[int, int] = (56, 68)

    def render(self):
        image = Image.new('1', self.size, 1)
        draw = ImageDraw.Draw(image)
        period = weather.get_current_period(self.office, self.grid)

        if self.type == 'temperature':
            self._render_temperature(image, draw, period)
        elif self.type == 'wind':
            self._render_wind(image, draw, period)
        elif self.type == 'forecast':
            self._render_forecast(image, draw, period)
        elif self.type == 'long_forecast':
            self._render_long_forecast(image, draw, period)
        else:
            raise ValueError(self.type)

        del draw
        self.serve(image)

    def _render_temperature(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_text(draw, self.font, f'{period.temperature}f', self.size,
                             horizontal_alignment='center',
                             vertical_alignment='middle')

    def _render_wind(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        text = f'{period.wind_speed}mph'

        if period.wind_speed == 0:
            drawing.aligned_text(draw, self.font, text, self.size,
                                 horizontal_alignment='center',
                                 vertical_alignment='middle')
            return

        text_size = draw.textsize(text, font=self.font)
        icon_size = (get_line_height(self.font), ) * 2

        icon_name = '-'.join(['arrow'] + [self._wind_direction_icon_map[token] for token in period.wind_direction])
        icon = drawing.get_icon(icon_name, icon_size)

        x_offset = int((self.size[0] - (icon.width + text_size[0])) / 2)

        image.paste(icon, (x_offset, int((self.size[1] / 2) - (icon.height / 2))))

        drawing.aligned_text(draw, self.font, text, self.size,
                             offset=(x_offset + icon.width, 0),
                             vertical_alignment='middle')

    def _render_forecast(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_wrapped_text(draw, self.font, period.short_forecast, self.size,
                                     horizontal_alignment='center')

    def _render_long_forecast(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_wrapped_text(draw, self.font, period.long_forecast, self.size,
                                     horizontal_alignment='center')

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> WeatherWorker:
        # noinspection PyTypeChecker
        worker: WeatherWorker = super().from_config(manager, config)

        worker.type = config.get('type', worker.type)
        worker.office = config.get('office', worker.office)
        worker.grid = config.get('grid', worker.grid)

        return worker

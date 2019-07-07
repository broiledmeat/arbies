from __future__ import annotations
from PIL import Image, ImageDraw
from typing import Tuple
from arbies.manager import Manager, ConfigDict
from arbies.workers import Worker
from arbies.suppliers import weather
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

        self.font_size: int = 16
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
        else:
            raise ValueError(self.type)

        del draw
        self.serve(image)

    def _render_temperature(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        font = drawing.get_font(size=self.font_size)
        drawing.aligned_text(draw, f'{period.temperature}f', self.size,
                             horizontal_alignment='center',
                             vertical_alignment='middle',
                             font=font)

    def _render_wind(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        font = drawing.get_font(size=self.font_size)

        text = f'{period.wind_speed}mph'

        if period.wind_speed == 0:
            drawing.aligned_text(draw, text, self.size,
                                 horizontal_alignment='center',
                                 vertical_alignment='middle',
                                 font=font)
            return

        text_size = draw.textsize(text, font=font)

        icon_name = '-'.join(['arrow'] + [self._wind_direction_icon_map[token] for token in period.wind_direction])
        icon = drawing.get_icon(icon_name, (self.font_size, self.font_size))

        x_offset = int((self.size[0] - (icon.width + text_size[0])) / 2)

        image.paste(icon, (x_offset, int((self.size[1] / 2) - (icon.height / 2))))

        drawing.aligned_text(draw, text, self.size,
                             offset=(x_offset + icon.width, 0),
                             vertical_alignment='middle',
                             font=font)

    def _render_forecast(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        font = drawing.get_font(size=self.font_size)
        drawing.aligned_text(draw, period.short_forecast, rect=self.size, horizontal_alignment='center', font=font)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> WeatherWorker:
        # noinspection PyTypeChecker
        worker: WeatherWorker = super().from_config(manager, config)

        worker.font_size = config.get('font_size', worker.font_size)
        worker.type = config.get('type', worker.type)
        worker.office = config.get('office', worker.office)
        worker.grid = config.get('grid', worker.grid)

        return worker

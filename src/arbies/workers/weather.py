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

        self.position = (0, 100)
        self.loop_interval = 30 * 60

        self.style = 'temperature'
        self.grid: weather.GpsCoords = weather.GpsCoords(42.865, -73.771)  # Albany

    def render(self):
        image = Image.new('1', self.size, 1)
        draw = ImageDraw.Draw(image)
        period = weather.get_current_period(self.grid)

        if self.style == 'temperature':
            self._render_temperature(image, draw, period)
        elif self.style == 'wind':
            self._render_wind(image, draw, period)
        elif self.style == 'forecast':
            self._render_forecast(image, draw, period)
        elif self.style == 'long_forecast':
            self._render_long_forecast(image, draw, period)
        else:
            raise ValueError(self.style)

        del draw
        self.serve(image)

    def _render_temperature(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_text(draw, self.font, f'{period.temperature}f', self.size,
                             horizontal_alignment=HorizontalAlignment.CENTER,
                             vertical_alignment=VerticalAlignment.CENTER)

    def _render_wind(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        text = f'{period.wind_speed}mph'

        if period.wind_speed == 0:
            drawing.aligned_text(draw, self.font, text, self.size,
                                 horizontal_alignment=HorizontalAlignment.CENTER,
                                 vertical_alignment=VerticalAlignment.CENTER)
            return

        text_size = draw.textsize(text, font=self.font)
        icon_size = (get_line_height(self.font), ) * 2

        icon_name = '-'.join(['arrow'] + [self._wind_direction_icon_map[token] for token in period.wind_direction])
        icon = drawing.get_icon(icon_name, icon_size)

        x_offset = int((self.size[0] - (icon.width + text_size[0])) / 2)

        image.paste(icon, (x_offset, int((self.size[1] / 2) - (icon.height / 2))))

        drawing.aligned_text(draw, self.font, text, self.size,
                             offset=(x_offset + icon.width, 0),
                             vertical_alignment=VerticalAlignment.CENTER)

    def _render_forecast(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_wrapped_text(draw, self.font, period.short_forecast, self.size,
                                     horizontal_alignment=HorizontalAlignment.CENTER)

    def _render_long_forecast(self, image: Image.Image, draw: ImageDraw.Draw, period: weather.WeatherPeriod):
        drawing.aligned_wrapped_text(draw, self.font, period.long_forecast, self.size,
                                     horizontal_alignment=HorizontalAlignment.CENTER)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> WeatherWorker:
        weather.init_from_config(manager.config)

        # noinspection PyTypeChecker
        worker: WeatherWorker = super().from_config(manager, config)

        worker.style = config.get('style', worker.style)

        if 'location' in config:
            worker.location = weather.get_location_coords(config['location'])
        elif 'locations' in manager.config and len(manager.config['locations']) >= 1:
            first_location = list(manager.config['locations'].keys())[0]
            worker.location = weather.get_location_coords(first_location)

        return worker

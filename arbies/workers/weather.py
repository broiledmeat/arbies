from PIL import Image, ImageDraw
from typing import Tuple
from arbies.manager import Manager
from arbies.workers import Worker
from arbies.suppliers import weather


class WeatherWorker(Worker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.position = (0, 100)
        self.loop_interval = 30 * 60

        self._office: str = 'ALY'
        self._grid: Tuple[int, int] = (56, 68)

    def render(self):
        period = weather.get_current_period(self._office, self._grid)
        image = Image.new('1', self.size, 1)
        draw = ImageDraw.Draw(image)

        draw.text((2, 0), f'{period.temperature}f')

        del draw
        self.serve(image)

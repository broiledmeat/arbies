from PIL import Image, ImageDraw
from typing import Tuple
from arbies.manager import Manager
from arbies.workers import Worker
from arbies.suppliers import datetime as adt
from arbies import drawing


class ClockWorker(Worker):
    _date_format: str = '%Y-%b-%d'
    _time_format: str = '%H:%M'

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.loop_interval = 0.5 * 60

        self._coords: Tuple[float, float] = (42.865, -73.771)

    def render(self):
        image = Image.new('1', self.size, 1)
        draw = ImageDraw.Draw(image)

        font = drawing.get_font()
        now = adt.now_tz()

        drawing.aligned_text(draw, (self.size[0] / 2, 0), now.strftime(self._date_format).upper(), 'center', font=font)
        drawing.aligned_text(draw, (self.size[0] / 2, 16), now.strftime(self._time_format), 'center', font=font)

        solar_day = adt.get_solar_day_info(self._coords)

        icon = drawing.get_icon('sun' if solar_day.sunrise <= now < solar_day.sunset else 'moon')
        image.paste(icon, (int((self.size[0] / 2) - (icon.width / 2)), 30))

        del draw
        self.serve(image)



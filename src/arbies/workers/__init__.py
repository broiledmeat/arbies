from __future__ import annotations
from abc import ABC
from collections import defaultdict
from threading import Timer
import time
import traceback
from PIL import Image, ImageDraw
from arbies import import_module_class_from_fullname
from arbies.manager import Manager, ConfigDict
from arbies.drawing import Font, get_font, as_color
from typing import TYPE_CHECKING, Type, Optional, Dict, Tuple, List

if TYPE_CHECKING:
    from arbies.drawing import ColorType


_registered: Dict[str, str] = {
    'datetime': 'arbies.workers.datetime.DateTimeWorker',
    'image': 'arbies.workers.image.ImageWorker',
    'networkstatus': 'arbies.workers.networkstatus.NetworkStatusWorker',
    'slideshow': 'arbies.workers.slideshow.SlideShowWorker',
    'solidrect': 'arbies.workers.solidrect.SolidRectWorker',
    'weather': 'arbies.workers.weather.WeatherWorker',
}


def get(name: str) -> Optional[Type]:
    return import_module_class_from_fullname(_registered[name.lower()])


class Worker(ABC):
    _instances: Dict[str, List[Worker]] = defaultdict(list)

    def __init__(self, manager: Manager):
        name = self.__class__.__name__
        if name.endswith(Worker.__name__):
            name = name[:-len(Worker.__name__)]

        Worker._instances[name].append(self)
        self.label = f'{name}[{len(Worker._instances[name]) - 1}]'

        self.manager: Manager = manager
        self.position: Tuple[int, int] = (0, 0)
        self.size: Tuple[int, int] = (100, 100)
        self.font: Font = get_font()
        self.font_fill: ColorType = (0, 0, 0, 255)

        self.loop_interval: Optional[float] = None
        self._loop_timer: Optional[Timer] = None

    def startup(self):
        pass

    def shutdown(self):
        self.cancel_loop()

    def loop(self):
        self.try_render()

        if self.loop_interval is None:
            return

        interval = self.loop_interval - time.time() % self.loop_interval

        self._loop_timer = Timer(interval, self.loop)
        self._loop_timer.start()

    def cancel_loop(self):
        if self._loop_timer is not None and self._loop_timer.is_alive():
            self._loop_timer.cancel()

    def render(self):
        raise NotImplemented

    def try_render(self):
        try:
            self.render()
        except BaseException:
            self._render_exceptioned()
            self.manager.log.error(traceback.format_exc())

    def _render_exceptioned(self):
        image = Image.new('RGBA', self.size, 1)
        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self.size[0], self.size[1]), (200, 200, 0, 128))

        for x in range(5, max(*self.size) * 2, 10):
            draw.line(((x, 0), (0, x)), (200, 0, 0), 2)

        del draw
        self.serve(image)

    def serve(self, image: Image.Image):
        self.manager.update_worker_image(self, image)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> Worker:
        worker = cls(manager)

        worker.size = config.get('Size', worker.size)
        worker.position = config.get('Position', worker.position)
        worker.font = get_font(config.get('Font', None), size=config.get('FontSize', None))
        worker.font_fill = as_color(config.get('FontFill', worker.font_fill))
        return worker

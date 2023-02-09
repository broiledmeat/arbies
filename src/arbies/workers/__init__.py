from __future__ import annotations
import asyncio
from abc import ABC
from collections import defaultdict
import traceback
from PIL import Image, ImageDraw
from arbies import import_module_class_from_fullname
from arbies.drawing import Font, get_font, as_color
from arbies.drawing.geometry import Vector2, Box
from arbies.manager import Manager, ConfigDict
from typing import TYPE_CHECKING, Type, Optional

if TYPE_CHECKING:
    from arbies.drawing import ColorType

_registered: dict[str, str] = {
    'datetime': 'arbies.workers.datetime_.DateTimeWorker',
    'image': 'arbies.workers.image.ImageWorker',
    'networkstatus': 'arbies.workers.networkstatus.NetworkStatusWorker',
    'slideshow': 'arbies.workers.slideshow.SlideShowWorker',
    'solidrect': 'arbies.workers.solidrect.SolidRectWorker',
    'weather': 'arbies.workers.weather.WeatherWorker',
}


def get(name: str) -> Optional[Type]:
    return import_module_class_from_fullname(_registered[name.lower()])


class Worker(ABC):
    _instances: dict[str, list[Worker]] = defaultdict(list)

    def __init__(self, manager: Manager):
        name = self.__class__.__name__
        if name.endswith(Worker.__name__):
            name = name[:-len(Worker.__name__)]

        Worker._instances[name].append(self)
        self.label = f'{name}[{len(Worker._instances[name]) - 1}]'

        self._manager: Manager = manager
        self._position: Vector2 = Vector2()
        self._size: Vector2 = Vector2(100, 100)
        self._font: Font = get_font()
        self._font_fill: ColorType = (0, 0, 0, 255)

    @property
    def manager(self):
        return self._manager

    @property
    def size(self) -> Vector2:
        return self._size

    @property
    def position(self) -> Vector2:
        return self._position

    @property
    def box(self) -> Box:
        return Box(self._position[0],
                   self._position[1],
                   self._position[0] + self._size[0],
                   self._position[1] + self._size[1])

    @property
    def font(self) -> Font:
        return self._font

    @property
    def font_fill(self) -> ColorType:
        return self._font_fill

    async def startup(self):
        pass

    async def shutdown(self):
        pass

    async def render_loop(self):
        await self.render_once()

    async def render_once(self):
        image: Image.Image

        try:
            image = await self._render_internal()
        except Exception:
            image = await self._render_exceptioned()
            self._manager.log.error(traceback.format_exc())

        await self._manager.update_worker_image(self, image)

    async def _render_internal(self) -> Image.Image:
        raise NotImplemented

    async def _render_exceptioned(self) -> Image.Image:
        image = Image.new('RGBA', self._size, 1)
        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, self._size[0], self._size[1]), (200, 200, 0, 128))

        for x in range(5, max(*self._size) * 2, 10):
            draw.line(((x, 0), (0, x)), (200, 0, 0), 2)

        del draw

        return image

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> Worker:
        worker = cls(manager)

        worker._size = Vector2(config.get('Size', worker._size))
        worker._position = Vector2(config.get('Position', worker._position))
        worker._font = get_font(config.get('Font', None), size=config.get('FontSize', None))
        worker._font_fill = as_color(config.get('FontFill', worker._font_fill))

        return worker


class LoopIntervalWorker(Worker):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._on_start: bool = True
        self._cron_interval: str = '*/1 * * * *'

    async def render_loop(self):
        from datetime import datetime
        from croniter import croniter

        if self._on_start:
            await self.render_once()

        delay: int = 0
        time_next: datetime = datetime.now()
        time_iter: croniter = croniter(self._cron_interval, time_next)
        while True:
            now = datetime.now()
            while time_next <= now or delay <= 0:
                time_next = time_iter.next(datetime)
                delay = (time_next - now).seconds
            self._manager.log.debug(f'Awaiting {self.label} until {time_next} ({delay} seconds)')
            await asyncio.sleep(delay)
            await self.render_once()

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> LoopIntervalWorker:
        # noinspection PyTypeChecker
        worker: LoopIntervalWorker = super().from_config(manager, config)

        worker._on_start = bool(config.get('OnStart', worker._on_start))
        worker._cron_interval = config.get('Interval', worker._cron_interval)

        return worker

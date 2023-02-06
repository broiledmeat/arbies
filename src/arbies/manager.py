from __future__ import annotations
import sys
import os
import asyncio
from datetime import datetime
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from PIL import Image, ImageDraw
from arbies.drawing.geometry import Vector2
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from arbies.drawing.geometry import Box
    from arbies.drawing import ColorType
    from arbies.trays import Tray
    from arbies.workers import Worker

ConfigDict = dict[str, Union[str, int, float, list, 'ConfigDict']]


class Manager:
    def __init__(self):
        self.config: ConfigDict = {}
        self.log: logging.Logger = logging.getLogger('arbies')
        self.trays: list[Tray] = []
        self.workers: list[Worker] = []

        self._size: Vector2 = Vector2(640, 384)
        self._image: Optional[Image.Image] = None
        self._background_fill: ColorType = 0

        self._worker_update_lock: asyncio.Lock = asyncio.Lock()
        self._worker_images: dict[Worker, Optional[Image.Image]] = {}
        self._updated_workers: set[Worker] = set()
        self._render_loop_interval: float = 15.0

        self.log.setLevel(logging.DEBUG)
        handler = StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        self.log.addHandler(handler)

        self._log_formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
        handler.setFormatter(self._log_formatter)

    @property
    def size(self) -> Vector2:
        return self._size

    @property
    def image(self) -> Image.Image:
        if self._image is None:
            self._image = Image.new('RGBA', self._size, self._background_fill)
        return self._image

    async def render_once(self):
        await self._startup()
        await asyncio.gather(*(worker.render_once() for worker in self.workers))

        for worker in self.workers:
            worker_image: Optional[Image.Image] = self._worker_images.get(worker, None)
            if worker_image is not None:
                self._composite_image(worker_image, self.image, worker.box)

        await asyncio.gather(*(tray.serve(self._image) for tray in self.trays))
        await self._shutdown()

    async def render_loop(self):
        await self._startup()
        worker_loops: tuple[asyncio.Task, ...] = tuple()

        try:
            manager_image = self.image
            worker_loops = tuple(asyncio.create_task(worker.render_loop()) for worker in self.workers)

            while True:
                # Wait until every HH:MM:??, where ?? is the seconds cleanly divisible by _render_loop_interval.
                await asyncio.sleep(self._render_loop_interval - (datetime.now().second % self._render_loop_interval))

                try:
                    await self._worker_update_lock.acquire()
                    updated_workers: list[Worker] = list(self._updated_workers)
                    updated_boxes: list[Box] = [worker.box for worker in self._updated_workers]

                    if len(updated_workers) == 0:
                        continue

                    self._updated_workers.clear()
                finally:
                    self._worker_update_lock.release()

                self._clear(self.image)
                for worker in self.workers:
                    worker_image: Optional[Image.Image] = self._worker_images.get(worker, None)
                    if worker_image is not None:
                        self._composite_image(worker_image, self.image, worker.box)

                # TODO: full or partial serve
                await asyncio.gather(*(tray.serve(manager_image, updated_boxes) for tray in self.trays))
        except asyncio.CancelledError:
            pass
        finally:
            for worker_loop in worker_loops:
                worker_loop.cancel()
            await asyncio.gather(*worker_loops)
            await self._shutdown()

    async def _startup(self):
        await asyncio.gather(*(tray.startup() for tray in self.trays))
        await asyncio.gather(*(worker.startup() for worker in self.workers))

    async def _shutdown(self):
        await asyncio.gather(*(worker.shutdown() for worker in self.workers))
        await asyncio.gather(*(tray.shutdown() for tray in self.trays))

    @staticmethod
    def _clear(target: Image.Image):
        draw = ImageDraw.Draw(target)
        draw.rectangle((0, 0, target.width, target.height), fill=(255, 255, 255, 255))

    @staticmethod
    def _paste_image(source: Image.Image, target: Image.Image, target_box: Box):
        target.paste(source, target_box)

    @staticmethod
    def _composite_image(source: Image.Image, target: Image.Image, target_box: Box):
        # Note: Image.Image.alpha_composite *would* be what we want here, but it is broken, as it attempts to
        # concatenate tuples.
        cropped = target.crop(target_box)
        composite = Image.alpha_composite(cropped, source)
        target.paste(composite, target_box)

    async def update_worker_image(self, worker: Worker, image: Image.Image):
        self.log.debug(f'Updating {worker.label}')
        self._worker_images[worker] = image

        try:
            await self._worker_update_lock.acquire()
            self._updated_workers.add(worker)
        finally:
            self._worker_update_lock.release()

    @classmethod
    def from_config(cls, config: ConfigDict) -> Manager:
        from arbies import trays, workers, drawing

        manager = cls()
        manager.config = config

        global_config: ConfigDict = config.get('Global', {})
        manager._size = tuple(global_config.get('Size', manager._size))
        manager._background_fill = global_config.get('BackgroundFill', manager._background_fill)

        log_path: Optional[str] = global_config.get('LogPath', None)
        if log_path is not None:
            handler = RotatingFileHandler(manager.resolve_path(log_path), maxBytes=2048)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(manager._log_formatter)
            manager.log.addHandler(handler)

        for item_name, item_config in config.get('Fonts', {}).items():
            drawing.Font.load_from_config(item_name, item_config)

        for section_name, module, manager_list in (('Trays', trays, manager.trays),
                                                   ('Workers', workers, manager.workers)):
            item_configs: list[ConfigDict] = config.get(section_name, {}).values()
            for item_config in item_configs:
                class_ = module.get(item_config['Type'])
                instance = class_.from_config(manager, item_config)
                manager_list.append(instance)

        return manager

    # noinspection PyMethodMayBeStatic
    def resolve_path(self, path: str) -> str:
        return os.path.expanduser(os.path.expandvars(path))

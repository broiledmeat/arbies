from __future__ import annotations
import sys
import os
import asyncio
from asyncio.exceptions import CancelledError
from datetime import datetime
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from PIL import Image, ImageDraw
from typing import TYPE_CHECKING, Type, Union

if TYPE_CHECKING:
    from arbies.drawing.geometry import Vector2, Box
    from arbies.drawing import ColorType
    from arbies.suppliers import Supplier
    from arbies.trays import Tray
    from arbies.workers import Worker

ConfigDict = dict[str, Union[str, int, float, list, 'ConfigDict']]


class Manager:
    def __init__(self, **kwargs):
        from arbies import trays, workers
        from arbies.drawing import as_color
        from arbies.drawing.font import Font
        from arbies.drawing.geometry import Vector2

        global_config: ConfigDict = kwargs.get('Global', {})

        # Rendering
        self._size: Vector2 = Vector2(global_config.get('Size', (640, 384)))
        self._background_fill: ColorType = as_color(global_config.get('BackgroundFill', (255, 255, 255)))
        self._render_loop_interval: float = 15.0
        self._image: Image.Image | None = None

        # Logging
        self.log: logging.Logger = logging.getLogger('arbies')
        self.log.setLevel(logging.DEBUG)
        handler = StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        self.log.addHandler(handler)

        self._log_formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
        handler.setFormatter(self._log_formatter)

        log_path: str | None = global_config.get('LogPath', None)
        if log_path is not None:
            handler = RotatingFileHandler(self.resolve_path(log_path), maxBytes=2048)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(self._log_formatter)
            self.log.addHandler(handler)

        # Fonts
        for item_name, item_config in kwargs.get('Fonts', {}).items():
            Font.load_from_config(item_name, item_config)

        # Suppliers
        self.suppliers: set[Supplier] = set()
        self._supplier_lock: asyncio.Lock = asyncio.Lock()

        # Worker updating
        self._worker_update_lock: asyncio.Lock = asyncio.Lock()
        self._worker_images: dict[Worker, Image.Image | None] = {}
        self._updated_workers: set[Worker] = set()

        # Trays and Workers
        self.config: ConfigDict = kwargs
        self.trays: list[Tray] = []
        self.workers: list[Worker] = []

        for section_name, module, manager_list in (('Trays', trays, self.trays),
                                                   ('Workers', workers, self.workers)):
            # noinspection PyTypeChecker
            item_configs: dict[str, ConfigDict] = kwargs.get(section_name, {})
            for item_name, item_config in item_configs.items():
                item_type = item_config.get('Type', None)

                if item_type is None:
                    raise KeyError(f"{section_name}.{item_name} has no Type parameter")

                class_ = module.get(item_type)

                if class_ is None:
                    raise KeyError(f"{section_name}.{item_name} has an unloadable Type parameter '{item_type}'")

                instance = class_(self, **item_config)
                manager_list.append(instance)

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
            worker_image: Image.Image | None = self._worker_images.get(worker, None)
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
                await self._worker_update_lock.acquire()

                try:
                    updated_workers: list[Worker] = list(self._updated_workers)
                    updated_boxes: list[Box] = [worker.box for worker in self._updated_workers]

                    if len(updated_workers) == 0:
                        continue

                    self._updated_workers.clear()
                finally:
                    self._worker_update_lock.release()

                self._clear(self.image)
                for worker in self.workers:
                    worker_image: Image.Image | None = self._worker_images.get(worker, None)
                    if worker_image is not None:
                        self._composite_image(worker_image, self.image, worker.box)

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
        try:
            await asyncio.gather(*(worker.shutdown() for worker in self.workers))
            await asyncio.gather(*(tray.shutdown() for tray in self.trays))
            await asyncio.gather(*(supplier.shutdown() for supplier in self.suppliers))
        except CancelledError:
            pass

    def _clear(self, target: Image.Image):
        draw = ImageDraw.Draw(target)
        draw.rectangle((0, 0, target.width, target.height), fill=self._background_fill)

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

        await self._worker_update_lock.acquire()

        try:
            self._worker_images[worker] = image
            self._updated_workers.add(worker)
        finally:
            self._worker_update_lock.release()

    async def get_supplier(self, type_: Type) -> Supplier:
        await self._supplier_lock.acquire()

        try:
            for supplier in self.suppliers:
                if type(supplier) == type_:
                    return supplier

            supplier: Supplier = type_(self)
            self.suppliers.add(supplier)
            await supplier.startup()
            return supplier
        finally:
            self._supplier_lock.release()

    # noinspection PyMethodMayBeStatic
    def resolve_path(self, path: str) -> str:
        return os.path.expanduser(os.path.expandvars(path))

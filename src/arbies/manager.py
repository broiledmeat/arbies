from __future__ import annotations
import sys
import os
from datetime import datetime
import time
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from PIL import Image
from typing import TYPE_CHECKING, Optional, Union, Dict, Tuple, List

if TYPE_CHECKING:
    from arbies.drawing import ColorType

ConfigDict = Dict[str, Union[str, int, float, List, 'ConfigDict']]


class Manager:
    def __init__(self):
        from arbies.trays import Tray
        from arbies.workers import Worker

        self.config: ConfigDict = {}
        self.log: logging.Logger = logging.getLogger('arbies')
        self.trays: List[Tray] = []
        self.workers: List[Worker] = []

        self.is_looping: bool = False
        self._is_cancelling_loop: bool = False

        self._size: Tuple[int, int] = (640, 384)
        self._image: Optional[Image.Image] = None
        self._background_fill: ColorType = 0

        self._update_worker_images: Dict[Worker, Image.Image] = {}

        self.log.setLevel(logging.DEBUG)
        handler = StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        self.log.addHandler(handler)

        self._log_formatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s')
        handler.setFormatter(self._log_formatter)

    @property
    def size(self):
        return tuple(self._size)

    def _startup(self):
        for tray in self.trays:
            tray.startup()

        for worker in self.workers:
            worker.startup()

    def _shutdown(self):
        for worker in self.workers:
            worker.shutdown()

        for tray in self.trays:
            tray.shutdown()

    def loop(self):
        self._startup()

        for worker in self.workers:
            worker.loop()

        self._loop()

    def cancel_loop(self):
        self._is_cancelling_loop = True

    def _loop(self):
        self.is_looping = True

        try:
            while not self._is_cancelling_loop:
                if len(self._update_worker_images) == 0:
                    time.sleep(1)
                    continue

                for worker, image in list(self._update_worker_images.items()):
                    self._image.paste(image, worker.position)
                    del self._update_worker_images[worker]

                time.sleep(3)

                if len(self._update_worker_images) > 0:
                    continue

                for tray in self.trays:
                    self.log.debug(f'[{datetime.now()}] Serving {tray.label}')
                    tray.serve(self._image)
        finally:
            self.is_looping = False
            self._is_cancelling_loop = False
            self._shutdown()

    def render_once(self):
        self._startup()

        for worker in self.workers:
            worker.try_render()

        image = self._get_image()
        for worker, worker_image in self._update_worker_images.items():
            # image.paste(worker_image, worker.position)
            # Note: Image.Image.alpha_composite is broken. It attempts to concatenate tuples.
            box = (worker.position[0],
                   worker.position[1],
                   worker.position[0] + worker.size[0],
                   worker.position[1] + worker.size[1])
            target = image.crop(box)
            composite = Image.alpha_composite(target, worker_image)
            image.paste(composite, box)

        for tray in self.trays:
            tray.serve(self._image)

        self._shutdown()

    def update_worker_image(self, worker, image: Image.Image):
        self.log.debug(f'Updating {worker.label}')
        self._update_worker_images[worker] = image

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
            handler.setLevel(logging.INFO)
            handler.setFormatter(manager._log_formatter)
            manager.log.addHandler(handler)

        for item_name, item_config in config.get('Fonts', {}).items():
            drawing.Font.load_from_config(item_name, item_config)

        for section_name, module, manager_list in (('Trays', trays, manager.trays),
                                                   ('Workers', workers, manager.workers)):
            item_configs: List[ConfigDict] = config.get(section_name, {}).values()
            for item_config in item_configs:
                class_ = module.get(item_config['Type'])
                instance = class_.from_config(manager, item_config)
                manager_list.append(instance)

        return manager

    def _get_image(self) -> Image.Image:
        if self._image is None:
            self._image = Image.new('RGBA', self._size, self._background_fill)
        return self._image

    # noinspection PyMethodMayBeStatic
    def resolve_path(self, path: str) -> str:
        return os.path.expanduser(os.path.expandvars(path))

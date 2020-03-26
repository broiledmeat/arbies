from __future__ import annotations
import sys
import os
from datetime import datetime
import importlib
import time
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from PIL import Image
from typing import Union, Dict, Tuple, List

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
        self._image = Image.new('1', self._size, 1)

        self._update_worker_images: Dict[Worker, Image.Image] = {}

        self.log.setLevel(logging.DEBUG)
        handler = StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        self.log.addHandler(handler)

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
                    self.log.info(f'[{datetime.now()}] Serving {tray.label}')
                    tray.serve(self._image)
        finally:
            self.is_looping = False
            self._is_cancelling_loop = False
            self._shutdown()

    def render_once(self):
        self._startup()

        for worker in self.workers:
            worker.render()

        for worker, image in self._update_worker_images.items():
            self._image.paste(image, worker.position)

        for tray in self.trays:
            tray.serve(self._image)

        self._shutdown()

    def update_worker_image(self, worker, image: Image.Image):
        self.log.info(f'[{datetime.now()}] Updating {worker.label}')
        self._update_worker_images[worker] = image

    @classmethod
    def from_config(cls, config: ConfigDict) -> Manager:
        from arbies.trays import Tray
        from arbies.workers import Worker
        from arbies.drawing import Font

        manager = cls()

        display_config: ConfigDict = config.get('display', {})
        manager._size = display_config.get('size', manager._size)

        log_config: ConfigDict = config.get('log', {})
        if 'path' in log_config:
            handler = RotatingFileHandler(Manager._resolve_path(log_config['path']), maxBytes=2048)
            handler.setLevel(logging.DEBUG)
            manager.log.addHandler(handler)

        for font_config in config.get('fonts', []):
            Font.load_from_config(font_config)

        for package_name, type_, manager_list in (('trays', Tray, manager.trays),
                                                  ('workers', Worker, manager.workers)):
            for item_config in config.get(package_name, []):
                name = item_config.get('name', None)

                if name is None:
                    raise ValueError(config)

                module = importlib.import_module(f'arbies.{package_name}.{name.lower()}')
                class_ = getattr(module, f'{name}{type_.__name__}')

                instance = class_.from_config(manager, item_config)

                manager_list.append(instance)

        manager.config = config

        return manager

    @staticmethod
    def _resolve_path(path: str) -> str:
        return os.path.expanduser(os.path.expandvars(path))

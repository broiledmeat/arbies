from __future__ import annotations
from datetime import datetime
import importlib
import time
from PIL import Image
from typing import Union, Dict, Tuple, List

ConfigDict = Dict[str, Union[str, int, float, List, 'ConfigDict']]


class Manager:
    def __init__(self):
        from arbies.trays import Tray
        from arbies.workers import Worker

        self.config: ConfigDict = {}
        self.trays: List[Tray] = []
        self.workers: List[Worker] = []

        self._size: Tuple[int, int] = (640, 384)
        self._image = Image.new('1', self._size, 1)

        self._update_worker_images: Dict[Worker, Image.Image] = {}

    def loop(self):
        for worker in self.workers:
            worker.loop()

        self._render_loop()

    def _render_loop(self):
        while True:
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
                print(f'[{datetime.now()}] Serving {tray.__class__.__name__}')
                tray.serve(self._image)

    def render_once(self):
        for worker in self.workers:
            worker.render()

        for worker, image in self._update_worker_images.items():
            self._image.paste(image, worker.position)

        for tray in self.trays:
            tray.serve(self._image)

    def update_worker_image(self, worker, image: Image.Image):
        print(f'[{datetime.now()}] Updating {worker.__class__.__name__}')
        self._update_worker_images[worker] = image

    @classmethod
    def from_config(cls, config: ConfigDict) -> Manager:
        from arbies.trays import Tray
        from arbies.workers import Worker

        manager = cls()

        display_config: ConfigDict = config.get('display', {})
        manager._size = display_config.get('size', manager._size)

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

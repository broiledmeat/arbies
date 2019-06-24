from __future__ import annotations
import os
import importlib
from PIL import Image
from typing import Union, Dict, Tuple, List

ConfigDict = Dict[str, Union[str, int, float, List, 'ConfigDict']]


class Manager:
    def __init__(self):
        from arbies.workers import Worker

        self.workers: List[Worker] = []
        self.config: ConfigDict = {}

        self._size: Tuple[int, int] = (640, 384)
        self._image = Image.new('1', self._size, 1)

        self._refresh_interval: int = 60
        self._update_worker_images: Dict[Worker, Image.Image] = {}

    def render_once(self):
        for worker in self.workers:
            worker.render()

        for worker, image in self._update_worker_images.items():
            self._image.paste(image, worker.position)

        path = os.path.abspath(f'./out.png')
        self._image.save(path, 'PNG')

    def update_worker_image(self, worker, image: Image.Image):
        self._update_worker_images[worker] = image

    @classmethod
    def from_config(cls, config: ConfigDict) -> Manager:
        from arbies.workers import Worker

        manager = cls()

        display_config: ConfigDict = config.get('display', {})
        manager._size = display_config.get('size', manager._size)
        manager._refresh_interval = display_config.get('refresh_interval', manager._refresh_interval)

        for worker_config in config.get('workers', []):
            name = worker_config.get('name', None)

            if name is None:
                continue

            module = importlib.import_module(f'arbies.workers.{name.lower()}')
            class_: Worker = getattr(module, f'{name}Worker')

            worker = class_.from_config(manager, worker_config)

            manager.workers.append(worker)

        manager.config = config

        return manager

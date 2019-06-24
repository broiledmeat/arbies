from __future__ import annotations
from PIL import Image
from threading import Timer
from typing import Optional, Tuple
from arbies.manager import Manager, ConfigDict


class Worker:
    def __init__(self, manager: Manager):
        self.manager: Manager = manager
        self.position: Tuple[int, int] = (0, 0)  # TODO: Load this from config
        self.size: Tuple[int, int] = (100, 100)  # TODO: Load this from config

        self.loop_interval: Optional[float] = None
        self._loop_timer: Optional[Timer] = None

    def loop(self):
        self.render()
        self._loop_timer = Timer(self.loop_interval, self.loop)
        self._loop_timer.start()

    def render(self):
        raise NotImplemented

    def serve(self, image: Image.Image):
        self.manager.update_worker_image(self, image)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> Worker:
        worker = cls(manager)

        worker.size = config.get('size', worker.size)
        worker.position = config.get('position', worker.position)

        return worker


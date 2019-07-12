from __future__ import annotations
from abc import ABC
from PIL import Image
from arbies.manager import Manager, ConfigDict


class Tray(ABC):
    def __init__(self, manager: Manager):
        self.manager = manager

    def startup(self):
        pass

    def shutdown(self):
        pass

    def serve(self, image: Image.Image):
        raise NotImplemented

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> Tray:
        return cls(manager)

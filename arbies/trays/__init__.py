from __future__ import annotations
from abc import ABC
from _collections import defaultdict
from PIL import Image
from arbies.manager import Manager, ConfigDict
from typing import Dict, List


class Tray(ABC):
    _instances: Dict[str, List[Tray]] = defaultdict(list)

    def __init__(self, manager: Manager):
        name = self.__class__.__name__
        if name.endswith(Tray.__name__):
            name = name[:-len(Tray.__name__)]

        Tray._instances[name].append(self)
        self.label = f'{name}[{len(Tray._instances[name]) - 1}]'

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

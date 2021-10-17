from __future__ import annotations
import os
from PIL import Image
from arbies.manager import Manager, ConfigDict
from . import Tray


class FileTray(Tray):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self.path: str = os.path.join(os.getcwd(), 'arbies.png')

    def serve(self, image: Image.Image):
        image.save(self.path, 'PNG')

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> FileTray:
        # noinspection PyTypeChecker
        tray: FileTray = super().from_config(manager, config)

        tray.path = os.path.abspath(os.path.expanduser(config.get('path', tray.path)))

        return tray

from __future__ import annotations
from abc import ABC
from _collections import defaultdict
from PIL import Image
from arbies import import_module_class_from_fullname
from arbies.drawing.geometry import Vector2, Box
from arbies.manager import Manager
from typing import Type


_registered: dict[str, str] = {
    'file': 'arbies.trays.file.FileTray',
    'framebuffer': 'arbies.trays.framebuffer.FramebufferTray',
    'tk': 'arbies.trays.tk.TkTray',
    'waveshareepd': 'arbies.trays.waveshareepd.WaveShareEPDTray',
    'waveshareit8951hat': 'arbies.trays.waveshareit8951hat.WaveShareIT8951HATTray',
}


def get(name: str) -> Type | None:
    type_path = _registered.get(name.lower(), None)

    if type_path is None:
        return None

    return import_module_class_from_fullname(type_path)


class Tray(ABC):
    _instances: dict[str, list[Tray]] = defaultdict(list)

    def __init__(self, manager: Manager, **kwargs):
        name = self.__class__.__name__
        if name.endswith(Tray.__name__):
            name = name[:-len(Tray.__name__)]

        Tray._instances[name].append(self)

        self._manager: Manager = manager
        self._label: str = f'{name}[{len(Tray._instances[name]) - 1}]'
        self._size: Vector2 = Vector2(kwargs.get('Size', manager.size))

    @property
    def size(self) -> Vector2:
        return self._size

    async def startup(self):
        pass

    async def shutdown(self):
        pass

    async def serve(self, image: Image.Image, updated_boxes: list[Box] | None = None):
        if self._size != image.size:
            if updated_boxes is not None:
                scale = (self._size[0] / image.size[0], self._size[1] / image.size[1])
                updated_boxes = [Box(box.x * scale[0], box.y * scale[1],
                                     box.w * scale[0], box.z * scale[1])
                                 for box in updated_boxes]
            image = image.resize(self._size)
        await self._serve_internal(image, updated_boxes)

    async def _serve_internal(self, image: Image.Image, updated_boxes: list[Box] | None = None):
        raise NotImplemented

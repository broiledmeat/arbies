from __future__ import annotations
from PIL import Image
from arbies.drawing.geometry import Box
from arbies.manager import Manager
from arbies.trays import Tray
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IT8951.display import AutoEPDDisplay


class WaveShareIT8951HATTray(Tray):
    _loop_interval = 60 * 60 * 24

    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._device: AutoEPDDisplay | None = None
        self._vcom: float = float(kwargs.get('Vcom', -1.0))

    async def startup(self):
        from IT8951.display import AutoEPDDisplay

        self._device = AutoEPDDisplay(vcom=self._vcom)
        self._device.clear()

    async def _serve_internal(self, image: Image.Image, updated_boxes: list[Box] | None = None):
        from IT8951.constants import DisplayModes

        self._device.frame_buf.paste(image)
        self._device.draw_partial(DisplayModes.GC16)

        self._manager.log.info(f'IT8951. Pushed full, 16 level grey, VCOM {self._vcom}.')

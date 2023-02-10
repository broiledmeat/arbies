from __future__ import annotations
from PIL import Image
from arbies.drawing.geometry import Box
from arbies.manager import Manager, ConfigDict
from arbies.trays import Tray
from arbies.trays.waveshareepd.device import Device, DeviceConfig


class WaveShareEPDTray(Tray):
    def __init__(self, manager: Manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._device: Device | None = None
        self._device_config: DeviceConfig = DeviceConfig(
            width=self.size.x,
            height=self.size.y,
            rst_pin=int(kwargs.get('RstPin', DeviceConfig.rst_pin)),
            dc_pin=int(kwargs.get('DcPin', DeviceConfig.dc_pin)),
            cs_pin=int(kwargs.get('CsPin', DeviceConfig.cs_pin)),
            busy_pin=int(kwargs.get('BusyPin', DeviceConfig.busy_pin)))

    async def startup(self):
        self._device = Device(self._device_config)
        self._device.init()

    def clear(self):
        self._device.try_locked(self._device.clear)

    async def _serve_internal(self, image: Image.Image, updated_boxes: list[Box] | None = None):
        self._image = image
        self._device.try_locked(lambda: self._device.display(self._image))

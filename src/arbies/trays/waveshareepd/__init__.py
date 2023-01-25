from __future__ import annotations
from typing import Optional
from PIL import Image
from arbies.manager import Manager, ConfigDict
from .. import Tray
from .device import Device, DeviceConfig


class WaveShareEPDTray(Tray):
    _loop_interval = 60 * 60 * 24

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._image: Optional[Image.Image] = None
        self._device_config: DeviceConfig = DeviceConfig(*manager.size)
        self._device: Optional[Device] = None

    async def startup(self):
        self._device = Device(self._device_config)
        self._device.init()

    def clear(self):
        self._device.try_locked(self._device.clear)

    async def serve(self, image: Image.Image, updated_boxes: Optional[list[Box]] = None):
        self._image = image
        self._device.try_locked(lambda: self._device.display(self._image))

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> WaveShareEPDTray:
        # noinspection PyTypeChecker
        tray: WaveShareEPDTray = super().from_config(manager, config)

        tray._device_config = DeviceConfig(
            width=config.get('Width', manager.size[0]),
            height=config.get('Height', manager.size[1]),
            rst_pin=config.get('RstPin', DeviceConfig.rst_pin),
            dc_pin=config.get('DcPin', DeviceConfig.dc_pin),
            cs_pin=config.get('CsPin', DeviceConfig.cs_pin),
            busy_pin=config.get('BusyPin', DeviceConfig.busy_pin),
        )

        return tray

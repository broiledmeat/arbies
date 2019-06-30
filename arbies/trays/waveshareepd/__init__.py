from __future__ import annotations
from PIL import Image
from arbies.manager import Manager, ConfigDict
from typing import Optional
from .. import Tray
from .device import Device, DeviceConfig


class WaveShareEPDTray(Tray):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._device_config: DeviceConfig = DeviceConfig(*manager.size)
        self._device: Optional[Device] = None

    def startup(self):
        self._device = Device(self._device_config)
        self._device.init()
        self._device.clear()

    def serve(self, image: Image.Image):
        self._device.display(image)

    @classmethod
    def from_config(cls, manager: Manager, config: ConfigDict) -> WaveShareEPDTray:
        # noinspection PyTypeChecker
        tray: WaveShareEPDTray = super().from_config(manager, config)

        tray._device_config = DeviceConfig(
            width=config.get('width', manager.size[0]),
            height=config.get('height', manager.size[1]),
            rst_pin=config.get('rst_pin', DeviceConfig.rst_pin),
            dc_pin=config.get('dc_pin', DeviceConfig.dc_pin),
            cs_pin=config.get('cs_pin', DeviceConfig.cs_pin),
            busy_pin=config.get('busy_pin', DeviceConfig.busy_pin),
        )

        return tray

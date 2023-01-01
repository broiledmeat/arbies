from __future__ import annotations
import time
from threading import Timer
from typing import Optional
from PIL import Image
from arbies.manager import Manager, ConfigDict
from .. import Tray
from .device import Device, DeviceConfig


class WaveShareEPDTray(Tray):
    _loop_interval = 60 * 60 * 24

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._loop_timer: Optional[Timer] = None
        self._image: Optional[Image.Image] = None
        self._device_config: DeviceConfig = DeviceConfig(*manager.size)
        self._device: Optional[Device] = None

    def startup(self):
        self._device = Device(self._device_config)
        self._device.init()
        self._loop()

    def shutdown(self):
        self.cancel_loop()

    def _loop(self):
        self.clear()

        if self._image is not None:
            self.serve(self._image)

        interval = self._loop_interval - time.time() % self._loop_interval

        self._loop_timer = Timer(interval, self._loop)
        self._loop_timer.start()

    def cancel_loop(self):
        if self._loop_timer is not None and self._loop_timer.is_alive():
            self._loop_timer.cancel()

    def clear(self):
        self._device.try_locked(self._device.clear)

    def serve(self, image: Image.Image):
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

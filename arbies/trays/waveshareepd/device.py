from dataclasses import dataclass
import time
from threading import Lock
from typing import Callable, List
from PIL import Image
import spidev
import RPi.GPIO as GPIO


@dataclass(frozen=True)
class DeviceConfig:
    width: int
    height: int
    rst_pin: int = 17
    dc_pin: int = 25
    cs_pin: int = 8
    busy_pin: int = 24


class Device:
    _PANEL_SETTING = 0x00
    _POWER_SETTING = 0x01
    _POWER_ON = 0x04
    _BOOSTER_SOFT_START = 0x06
    _DATA_START_TRANSMISSION_1 = 0x10
    _DISPLAY_REFRESH = 0x12
    _PLL_CONTROL = 0x30
    _TEMPERATURE_CALIBRATION = 0x41
    _VCOM_AND_DATA_INTERVAL_SETTING = 0x50
    _TCON_SETTING = 0x60
    _TCON_RESOLUTION = 0x61
    _VCM_DC_SETTING = 0x82
    _FLASH_MODE = 0xe5

    def __init__(self, config: DeviceConfig):
        self._config = config
        self._spi = spidev.SpiDev(0, 0)

    def reset(self):
        self._digital_write(self._config.rst_pin, GPIO.HIGH)
        self._delay_ms(200)
        self._digital_write(self._config.rst_pin, GPIO.LOW)
        self._delay_ms(200)
        self._digital_write(self._config.rst_pin, GPIO.HIGH)
        self._delay_ms(200)

    def init(self):
        self._module_init()
        self.reset()

        self._send_command(self._POWER_SETTING)
        self._send_data(0x37)
        self._send_data(0x00)
        self._send_command(self._PANEL_SETTING)
        self._send_data(0xcf)
        self._send_data(0x08)
        self._send_command(self._BOOSTER_SOFT_START)
        self._send_data(0xc7)
        self._send_data(0xcc)
        self._send_data(0x28)
        self._send_command(self._POWER_ON)
        self._wait_until_idle()
        self._send_command(self._PLL_CONTROL)
        self._send_data(0x3c)
        self._send_command(self._TEMPERATURE_CALIBRATION)
        self._send_data(0x00)
        self._send_command(self._VCOM_AND_DATA_INTERVAL_SETTING)
        self._send_data(0x77)
        self._send_command(self._TCON_SETTING)
        self._send_data(0x22)
        self._send_command(self._TCON_RESOLUTION)
        self._send_data(self._config.width >> 8)
        self._send_data(self._config.width & 0xff)
        self._send_data(self._config.height >> 8)
        self._send_data(self._config.height & 0xff)
        self._send_command(self._VCM_DC_SETTING)
        self._send_data(0x1e)
        self._send_command(self._FLASH_MODE)
        self._send_data(0x03)

    def clear(self):
        self._send_command(self._DATA_START_TRANSMISSION_1)
        for i in range((self._config.width // 4 * self._config.height) * 4):
            self._send_data(0x33)
        self._send_command(self._DISPLAY_REFRESH)
        self._wait_until_idle()

    def display(self, image: Image.Image):
        buffer = self._get_buffer(image)

        self._send_command(self._DATA_START_TRANSMISSION_1)

        for value in buffer:
            self._send_data(value)

        self._send_command(self._DISPLAY_REFRESH)
        self._delay_ms(100)
        self._wait_until_idle()

    def _get_buffer(self, image: Image.Image) -> List[int]:
        width, height = self._config.width, self._config.height
        buffer = [0x00] * (width * height // 2)
        pixels = image.load()

        for y in range(height):
            for x in range(0, width, 2):
                i = (x + y * width) // 2
                if pixels[x + 0, y] != 0:
                    buffer[i] |= 0x30  # 00110000
                if pixels[x + 1, y] != 0:
                    buffer[i] |= 0x03  # 00000011

        return buffer

    def _wait_until_idle(self):
        while self._digital_read(self._config.busy_pin) == 0:
            self._delay_ms(100)

    def _send_command(self, command: int):
        self._digital_write(self._config.dc_pin, GPIO.LOW)
        self._spi.writebytes([command])

    def _send_data(self, data: int):
        self._digital_write(self._config.dc_pin, GPIO.HIGH)
        self._spi.writebytes([data])

    @staticmethod
    def _digital_write(pin: int, value: int):
        GPIO.output(pin, value)

    @staticmethod
    def _digital_read(pin: int):
        return GPIO.input(pin)

    @staticmethod
    def _delay_ms(delay: float):
        time.sleep(delay / 1000.0)

    def _module_init(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._config.rst_pin, GPIO.OUT)
        GPIO.setup(self._config.dc_pin, GPIO.OUT)
        GPIO.setup(self._config.cs_pin, GPIO.OUT)
        GPIO.setup(self._config.busy_pin, GPIO.IN)
        self._spi.max_speed_hz = 2000000
        self._spi.mode = 0b00

    _lock = Lock()

    class AcquireLockError(RuntimeError):
        pass

    def try_locked(self, func: Callable, blocking=False):
        if not self._lock.acquire(blocking=blocking):
            return

        try:
            func()
        finally:
            self._lock.release()

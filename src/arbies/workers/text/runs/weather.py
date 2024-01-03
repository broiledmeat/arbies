from __future__ import annotations
from enum import Enum
from arbies.manager import Manager
from arbies.workers.text.runs import Run
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arbies.suppliers.weather import WeatherPeriod


class Units(Enum):
    METRIC = 1
    IMPERIAL = 2


class _Weather(Run):
    name: str | None = None

    def __init__(self, *params: str):
        super().__init__(*params)

        self.location: str | None = None
        self.units: Units = Units.METRIC

        units = 'm'
        if len(params) == 1:
            units = params[0]
        elif len(params) >= 2:
            self.location = params[0]
            units = params[1]

        self.units = Units.METRIC if units.lower() != 'i' else Units.IMPERIAL

    async def render(self, manager: Manager):
        from arbies.suppliers.location import LocationSupplier
        from arbies.suppliers.weather import WeatherSupplier

        location_supplier: LocationSupplier = await manager.get_supplier(LocationSupplier)
        weather_supplier: WeatherSupplier = await manager.get_supplier(WeatherSupplier)

        location = location_supplier.get(self.location)
        period = await weather_supplier.get_current(location.coords)

        return self._get_str(period)

    def _get_str(self, period: WeatherPeriod):
        raise NotImplemented


class WeatherTemperature(_Weather):
    name: str | None = 'weather.temp'

    def _get_str(self, period: WeatherPeriod):
        temperature = period.temperature

        if self.units == Units.METRIC:
            temperature = (temperature - 32) / 1.8

        return str(int(temperature))


class WeatherForecast(_Weather):
    name: str | None = 'weather.forecast'

    def _get_str(self, period: WeatherPeriod):
        return period.short_forecast


class WeatherWindDirection(_Weather):
    name: str | None = 'weather.winddirection'

    def _get_str(self, period: WeatherPeriod):
        return period.wind_direction


class WeatherWindSpeed(_Weather):
    name: str | None = 'weather.windspeed'

    def _get_str(self, period: WeatherPeriod):
        return period.wind_speed
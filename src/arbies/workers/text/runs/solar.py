from __future__ import annotations
from arbies.manager import Manager
from arbies.workers.text.runs.datetime import DateTime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arbies.suppliers.solar import SolarInfo


class _Solar(DateTime):
    name: str | None = None

    async def render(self, manager: Manager):
        from arbies.suppliers.datetime_ import DateTimeSupplier
        from arbies.suppliers.location import LocationSupplier
        from arbies.suppliers.solar import SolarSupplier

        location_supplier: LocationSupplier = await manager.get_supplier(LocationSupplier)
        datetime_supplier: DateTimeSupplier = await manager.get_supplier(DateTimeSupplier)
        solar_supplier: SolarSupplier = await manager.get_supplier(SolarSupplier)

        location = location_supplier.get(self.location)
        now = datetime_supplier.now_tz(location.timezone)
        solar_info = await solar_supplier.get_solar_info(now, location.coords)

        return self._get_str(solar_info)

    def _get_str(self, solar_info: SolarInfo):
        raise NotImplemented


class SolarSunRise(_Solar):
    name: str | None = 'solar.sunrise'

    def _get_str(self, solar_info: SolarInfo):
        return solar_info.sunrise.strftime(self.format)


class SolarSunSet(_Solar):
    name: str | None = 'solar.sunset'

    def _get_str(self, solar_info: SolarInfo):
        return solar_info.sunset.strftime(self.format)
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo
import json
from string import Template
from arbies.asyncutil import ContextLock
from arbies.manager import Manager
from arbies.suppliers import Supplier
from arbies.suppliers.location import Coords


@dataclass(frozen=True)
class SolarInfo:
    day_length: timedelta
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime

    def as_tz(self, tz: tzinfo | None):
        return SolarInfo(
            day_length=self.day_length,
            sunrise=self.sunrise.astimezone(tz),
            sunset=self.sunset.astimezone(tz),
            solar_noon=self.solar_noon.astimezone(tz))


class SolarSupplier(Supplier):
    _cache_expire_time: int = 30 * 60
    _sunrise_uri: Template = Template('https://api.sunrise-sunset.org/json?lat=$latitude&lng=$longitude&formatted=0')

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._cache_locks = ContextLock()
        self._solar_info_cache: dict[Coords, tuple[datetime, SolarInfo]] = {}

    async def get_solar_info(self, time: datetime, coords: Coords, tz: tzinfo | None = None) -> SolarInfo:
        async with self._cache_locks.acquire(coords):
            solar_info: SolarInfo

            if coords not in self._solar_info_cache or time.date() != self._solar_info_cache[coords][0].date():
                solar_info = await self._get_solar_info(coords)
                self._solar_info_cache[coords] = (time, solar_info)
            else:
                solar_info = self._solar_info_cache[coords][1]

            return solar_info.as_tz(tz)

    @staticmethod
    async def _get_solar_info(coords: Coords) -> SolarInfo:
        uri = SolarSupplier._sunrise_uri.substitute(latitude=coords.latitude, longitude=coords.longitude)
        async with aiohttp.ClientSession() as session, session.get(uri) as response:
            if response.status != 200:
                raise IOError(f'Weather service returned {response.status}: {response.content}')

            try:
                data = json.loads(await response.text())['results']
            except json.JSONDecodeError:
                raise ValueError(f'DateTime service returned unparseable response: {response.content}')

            return SolarInfo(
                day_length=timedelta(seconds=data['day_length']),
                sunrise=datetime.fromisoformat(data['sunrise']),
                sunset=datetime.fromisoformat(data['sunset']),
                solar_noon=datetime.fromisoformat(data['solar_noon']))

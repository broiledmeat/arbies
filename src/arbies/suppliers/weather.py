import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
import json
from string import Template
import aiohttp
from arbies.manager import Manager
from arbies.suppliers import Supplier
from arbies.suppliers.location import Coords


@dataclass(frozen=True)
class GridCoords:
    office: str
    x: int
    y: int


@dataclass(frozen=True)
class WeatherPeriod:
    name: str
    start_time: datetime
    end_time: datetime
    is_daytime: bool
    short_forecast: str
    long_forecast: str
    temperature: float  # fahrenheit
    wind_direction: str
    wind_speed: float  # mph


class WeatherSupplier(Supplier):
    _cache_expire_time: int = 30 * 60
    _gps_grid_lookup_uri: Template = Template('https://api.weather.gov/points/$latitude,$longitude')
    _weather_weekly_uri: Template = Template('https://api.weather.gov/gridpoints/$office/$gridx,$gridy/forecast')
    _weather_hourly_uri: Template = Template('https://api.weather.gov/gridpoints/$office/$gridx,$gridy/forecast/hourly')

    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._cache_lock: asyncio.Lock = asyncio.Lock()
        self._cache_locks: dict[Coords, asyncio.Lock] = {}
        self._coords_grid_lookup: dict[Coords, GridCoords] = {}
        self._periods_cache: dict[GridCoords, tuple[datetime, WeatherPeriod]] = {}

    async def get_current(self, coords: Coords) -> WeatherPeriod:
        from arbies.suppliers.datetime_ import now_tz

        async with self._acquire_cache_lock(coords):
            if coords not in self._coords_grid_lookup:
                self._coords_grid_lookup[coords] = await self._get_gps_grid(coords)
            grid = self._coords_grid_lookup[coords]
            now = now_tz()

            if coords in self._periods_cache and \
                    (now - self._periods_cache[grid][0]).total_seconds() < self._cache_expire_time:
                return self._periods_cache[grid][1]

            weekly_period_task = self._get_current_raw_period(self._weather_weekly_uri, grid)
            hourly_period_task = self._get_current_raw_period(self._weather_hourly_uri, grid)

            weekly_period: WeatherPeriod = await weekly_period_task
            hourly_period: WeatherPeriod = await hourly_period_task

            period: WeatherPeriod = WeatherPeriod(
                name='Now',
                start_time=hourly_period.start_time,
                end_time=hourly_period.end_time,
                is_daytime=hourly_period.is_daytime,
                short_forecast=hourly_period.short_forecast,
                long_forecast=weekly_period.long_forecast,
                temperature=hourly_period.temperature,
                wind_direction=hourly_period.wind_direction,
                wind_speed=hourly_period.wind_speed
            )

            self._periods_cache[grid] = (now, period)

        return period

    @asynccontextmanager
    async def _acquire_cache_lock(self, coords: Coords):
        await self._cache_lock.acquire()

        if coords not in self._cache_locks:
            self._cache_locks[coords] = asyncio.Lock()
        lock = self._cache_locks[coords]

        self._cache_lock.release()

        try:
            await lock.acquire()
            yield lock
        finally:
            lock.release()

    @staticmethod
    async def _get_gps_grid(coords: Coords) -> GridCoords:
        uri = WeatherSupplier._gps_grid_lookup_uri.substitute(latitude=coords.latitude, longitude=coords.longitude)
        async with aiohttp.ClientSession() as session, session.get(uri) as response:
            if response.status != 200:
                raise IOError(f'Weather service returned {response.status}: {response.content}')

            try:
                data = json.loads(await response.text())
            except json.JSONDecodeError:
                raise ValueError(f'Weather service returned unparseable response: {response.content}')

            return GridCoords(data['properties']['cwa'],
                              data['properties']['gridX'],
                              data['properties']['gridY'])

    @staticmethod
    async def _get_current_raw_period(uri_template: Template, grid: GridCoords) -> WeatherPeriod:
        uri = uri_template.substitute(office=grid.office, gridx=grid.x, gridy=grid.y)
        async with aiohttp.ClientSession() as session, session.get(uri) as response:
            if response.status != 200:
                raise IOError(f'Weather service returned {response.status}: {response.content}')

            try:
                data = json.loads(await response.text())
            except json.JSONDecodeError:
                raise ValueError(f'Weather service returned unparseable response: {response.content}')

            period = data['properties']['periods'][0]

            wind_tokens = str(period['windSpeed']).split()
            wind_speed = int(wind_tokens[0])

            return WeatherPeriod(
                name=period['name'],
                start_time=datetime.fromisoformat(period['startTime']),
                end_time=datetime.fromisoformat(period['endTime']),
                is_daytime=period['isDaytime'],
                short_forecast=period['shortForecast'],
                long_forecast=period['detailedForecast'],
                temperature=period['temperature'],
                wind_direction=period['windDirection'],
                wind_speed=wind_speed
            )

from dataclasses import dataclass
from datetime import datetime
import json
from string import Template
import requests
from arbies.manager import ConfigDict
from typing import Dict, Tuple


@dataclass(frozen=True)
class GpsCoords:
    latitude: float
    longitude: float


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


_gps_grid_lookup_uri: Template = Template('https://api.weather.gov/points/$latitude,$longitude')
_weather_weekly_uri: Template = Template('https://api.weather.gov/gridpoints/$office/$gridx,$gridy/forecast')
_weather_hourly_uri: Template = Template('https://api.weather.gov/gridpoints/$office/$gridx,$gridy/forecast/hourly')

_locations: Dict[str, GpsCoords] = {}
_coordinates_grid_lookup: Dict[GpsCoords, GridCoords] = {}
_periods_cache: Dict[GridCoords, Tuple[datetime, WeatherPeriod]] = {}
_cache_expire_time: int = 30 * 60


def init_from_config(config: ConfigDict):
    for name, location_config in config.get('locations', {}).items():
        if name not in location_config:
            _locations[name] = location_config['coords']


def get_location_coords(name: str) -> GpsCoords:
    return _locations[name]


def get_current_period(coords: GpsCoords) -> WeatherPeriod:
    from arbies.suppliers.datetime import now_tz

    if coords not in _coordinates_grid_lookup:
        _coordinates_grid_lookup[coords] = _get_gps_grid(coords)

    grid = _coordinates_grid_lookup[coords]
    now = now_tz()

    if coords in _periods_cache and (now - _periods_cache[grid][0]).total_seconds() < _cache_expire_time:
        return _periods_cache[grid][1]

    weekly_period: WeatherPeriod = _get_current_raw_period(_weather_weekly_uri, grid)
    hourly_period: WeatherPeriod = _get_current_raw_period(_weather_hourly_uri, grid)

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

    _periods_cache[grid] = (now, period)

    return period


def _get_gps_grid(coords: GpsCoords) -> GridCoords:
    response = requests.get(_gps_grid_lookup_uri.substitute(latitude=coords.latitude, longitude=coords.longitude))

    if response.status_code != 200:
        raise IOError(f'Weather service returned {response.status_code}: {response.content}')

    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        raise ValueError(f'Weather service returned unparseable response: {response.content}')

    return GridCoords(data['properties']['cwa'],
                      data['properties']['gridX'],
                      data['properties']['gridY'])


def _get_current_raw_period(uri_template: Template, grid: GridCoords) -> WeatherPeriod:
    response = requests.get(uri_template.substitute(office=grid.office, gridx=grid.x, gridy=grid.y))

    if response.status_code != 200:
        raise IOError(f'Weather service returned {response.status_code}: {response.content}')

    try:
        data = json.loads(response.content)
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

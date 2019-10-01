from dataclasses import dataclass
from datetime import datetime
import json
import requests
from typing import Dict, Tuple


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


_weather_daily_uri: str = 'https://api.weather.gov/gridpoints/{}/{},{}/forecast'
_weather_hourly_uri: str = 'https://api.weather.gov/gridpoints/{}/{},{}/forecast/hourly'
_weather_period_cache: Dict[Tuple[str, int, int], Tuple[datetime, WeatherPeriod]] = {}
_cache_expire_time: int = 30 * 60


def get_current_period(office: str, grid: Tuple[int, int]) -> WeatherPeriod:
    from arbies.suppliers.datetime import now_tz

    now = now_tz()
    key = (office, grid[0], grid[1])

    if key in _weather_period_cache and (now - _weather_period_cache[key][0]).total_seconds() < _cache_expire_time:
        return _weather_period_cache[key][1]

    daily_period: WeatherPeriod = _get_current_period(_weather_daily_uri, office, grid)
    hourly_period: WeatherPeriod = _get_current_period(_weather_hourly_uri, office, grid)

    period: WeatherPeriod = WeatherPeriod(
        name='Now',
        start_time=hourly_period.start_time,
        end_time=hourly_period.end_time,
        is_daytime=hourly_period.is_daytime,
        short_forecast=hourly_period.short_forecast,
        long_forecast=daily_period.long_forecast,
        temperature=hourly_period.temperature,
        wind_direction=hourly_period.wind_direction,
        wind_speed=hourly_period.wind_speed
    )

    _weather_period_cache[key] = (now, period)

    return period


def _get_current_period(uri: str, office: str, grid: Tuple[int, int]) -> WeatherPeriod:
    # TODO: This is not safe.
    response = requests.get(uri.format(office, *grid))
    data = json.loads(response.content)

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

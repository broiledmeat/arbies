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


_weather_uri: str = 'https://api.weather.gov/gridpoints/{}/{},{}/forecast'
_weather_period_cache: Dict[Tuple[str, int, int], Tuple[datetime, WeatherPeriod]] = {}


def get_current_period(office: str, grid: Tuple[int, int]) -> WeatherPeriod:
    from arbies.suppliers.datetime import now_tz

    now = now_tz()
    key = (office, grid[0], grid[1])

    if key in _weather_period_cache and (now - _weather_period_cache[key][0]).total_seconds() < 30 * 60 * 60:
        return _weather_period_cache[key][1]

    # TODO: This is *way* not safe.
    response = requests.get(_weather_uri.format(office, *grid))
    data = json.loads(response.content)

    period = data['properties']['periods'][0]

    wind_tokens = str(period['windSpeed']).split()
    wind_speed = int(wind_tokens[0])

    period = WeatherPeriod(
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

    _weather_period_cache[key] = (now, period)

    return period

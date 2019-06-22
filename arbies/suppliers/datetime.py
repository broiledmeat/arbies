from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
import json
from typing import Optional, Dict, Tuple
import requests


@dataclass(frozen=True)
class SolarDayInfo:
    day_length: timedelta
    sunrise: datetime
    sunset: datetime
    solar_noon: datetime


_sunrise_uri: str = 'http://api.sunrise-sunset.org/json?lat={}&lng={}&formatted=0'
_solar_day_info_cache: Dict[Tuple[float, float], Tuple[datetime, SolarDayInfo]] = {}


def now_tz(tz: Optional[tzinfo] = None) -> datetime:
    return datetime.now(timezone.utc).astimezone(tz=tz)


def get_solar_day_info(coords: Tuple[float, float]) -> SolarDayInfo:
    now = now_tz()

    if coords in _solar_day_info_cache and (now - _solar_day_info_cache[coords][0]).days < 1:
        return _solar_day_info_cache[coords][1]

    response = requests.get(_sunrise_uri.format(*coords))
    data = json.loads(response.content)['results']

    solar_info = SolarDayInfo(
        day_length=timedelta(seconds=data['day_length']),
        sunrise=datetime.fromisoformat(data['sunrise']),
        sunset=datetime.fromisoformat(data['sunset']),
        solar_noon=datetime.fromisoformat(data['solar_noon'])
    )

    _solar_day_info_cache[coords] = (now, solar_info)

    return solar_info

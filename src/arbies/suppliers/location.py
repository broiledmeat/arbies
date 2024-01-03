from __future__ import annotations
from dataclasses import dataclass
from pytz import timezone
from arbies.manager import Manager
from arbies.suppliers import Supplier


@dataclass(frozen=True)
class Coords:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Location:
    name: str
    timezone: timezone
    coords: Coords


class LocationSupplier(Supplier):
    def __init__(self, manager: Manager):
        super().__init__(manager)

        self._locations: set[Location] = set()
        self._default_location: Location | None = None

    async def startup(self):
        for name, location_config in self.manager.config.get('Locations', {}).items():
            timezone_ = timezone(location_config.get('Timezone'))
            coords = tuple(location_config.get('Coords'))
            location = Location(name, timezone_, Coords(float(coords[0]), float(coords[1])))
            self._locations.add(location)

            if self._default_location is None:
                self._default_location = location

    def get(self, name: str | None = None):
        if name is None:
            if self._default_location is not None:
                return self._default_location
            raise ValueError('No locations specified. Cannot get a default.')

        for location in self._locations:
            if location.name == name:
                return location

        raise ValueError(f'No location with name "{name}".')

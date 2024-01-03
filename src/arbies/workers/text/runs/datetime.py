from arbies.manager import Manager
from arbies.workers.text.runs import Run


class DateTime(Run):
    name: str | None = 'dt.now'

    def __init__(self, *params: str):
        super().__init__(*params)

        self.location: str | None = None
        self.format: str = '%Y-%m-%d %H:%M'

        if len(params) == 1:
            self.format = params[0]
        elif len(params) >= 2:
            self.location = params[0]
            self.format = '|'.join(params[1:])

    async def render(self, manager: Manager):
        from arbies.suppliers.datetime_ import DateTimeSupplier
        from arbies.suppliers.location import LocationSupplier

        location_supplier: LocationSupplier = await manager.get_supplier(LocationSupplier)
        datetime_supplier: DateTimeSupplier = await manager.get_supplier(DateTimeSupplier)

        location = location_supplier.get(self.location)
        now = datetime_supplier.now_tz(location.timezone)

        return now.strftime(self.format)

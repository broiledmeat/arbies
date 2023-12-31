from datetime import datetime, timezone, tzinfo
from arbies.suppliers import Supplier


class DateTimeSupplier(Supplier):
    @staticmethod
    def now_tz(tz: tzinfo | None = None) -> datetime:
        return datetime.now(timezone.utc).astimezone(tz=tz)

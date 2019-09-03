from __future__ import annotations
from enum import Enum
from typing import Union


class _ConvertFromEnumMixin:
    @classmethod
    def convert_from(cls, value: Union[_ConvertFromEnumMixin, int, str]) -> _ConvertFromEnumMixin:
        if isinstance(value, _ConvertFromEnumMixin):
            return value
        if isinstance(value, int):
            # noinspection PyArgumentList
            return cls(value)
        if isinstance(value, str):
            return cls[value.strip().upper()]


class HorizontalAlignment(_ConvertFromEnumMixin, Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


class VerticalAlignment(_ConvertFromEnumMixin, Enum):
    TOP = 0
    CENTER = 1
    BOTTOM = 2

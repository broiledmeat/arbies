from __future__ import annotations
from enum import Enum


type Vector2Type = tuple[float, float]
type ColorType = str | tuple[int, int, int] | tuple[int, int, int, int]


class _ConvertFromEnumMixin:
    @classmethod
    def convert_from(cls, value: _ConvertFromEnumMixin | int | str) -> _ConvertFromEnumMixin:
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


def get_aligned_position(section: Vector2Type,
                         area: Vector2Type,
                         horizontal_alignment: HorizontalAlignment,
                         vertical_alignment: VerticalAlignment
                         ) -> Vector2Type:
    if horizontal_alignment == HorizontalAlignment.LEFT:
        x = 0
    elif horizontal_alignment == HorizontalAlignment.CENTER:
        x = (area[0] - section[0]) / 2
    elif horizontal_alignment == HorizontalAlignment.RIGHT:
        x = area[0] - section[0]
    else:
        raise ValueError(horizontal_alignment)

    if vertical_alignment == VerticalAlignment.TOP:
        y = 0
    elif vertical_alignment == VerticalAlignment.CENTER:
        y = (area[1] - section[1]) / 2
    elif vertical_alignment == VerticalAlignment.BOTTOM:
        y = area[1] - section[1]
    else:
        raise ValueError(vertical_alignment)

    return x, y

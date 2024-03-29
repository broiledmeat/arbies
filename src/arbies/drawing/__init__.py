from __future__ import annotations
import os
import io
from PIL import Image, ImageColor
import cairosvg
from arbies.drawing._consts import Vector2Type, ColorType, HorizontalAlignment, VerticalAlignment, get_aligned_position
from typing import Callable, Iterable

_icon_cache: dict[tuple[str, Vector2Type], Image.Image] = {}


def get_icon(name: str, size: Vector2Type | None = None) -> Image.Image:
    size: Vector2Type = size or (32, 32)
    key = (name, size)

    if key in _icon_cache:
        return _icon_cache[key]

    stream = io.BytesIO()
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../../../resources/icons/{name}.svg'))

    cairosvg.svg2png(url=path, write_to=stream, output_width=size[0], output_height=size[1])

    image = Image.open(stream)
    image.load()

    _icon_cache[key] = image

    return image


def draw_image(dest: Image.Image,
               source: Image.Image,
               area: Vector2Type | None = None,
               offset: Vector2Type | None = None,
               resize: bool = False,
               horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
               vertical_alignment: VerticalAlignment = VerticalAlignment.TOP,
               pre_processors: Iterable[Callable[[Image.Image], Image.Image]] | None = None,
               post_processors: Iterable[Callable[[Image.Image], Image.Image]] | None = None):
    area = area or dest.size

    for processor in (pre_processors or []):
        source = processor(source)

    if resize:
        source = source.copy()
        source.thumbnail(area, Image.LANCZOS if source.size > area else Image.BICUBIC)

    for processor in (post_processors or []):
        source = processor(source)

    x, y = get_aligned_position(source.size, area, horizontal_alignment, vertical_alignment)

    if offset is not None:
        x += offset[0]
        y += offset[1]

    dest.paste(source, (int(x), int(y)))


def as_color(value: ColorType) -> ColorType:
    if isinstance(value, tuple) and 3 <= len(value) <= 4:
        return value
    elif isinstance(value, list) and 3 <= len(value) <= 4:
        return tuple(value)
    elif isinstance(value, str):
        return ImageColor.getrgb(value)
    raise ValueError(value)

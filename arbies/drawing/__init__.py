from __future__ import annotations
import os
import io
from PIL import Image, ImageFont, ImageOps
import cairosvg
from typing import Callable, Optional, Iterable, Tuple, Dict
from ._consts import Vector2Type, HorizontalAlignment, VerticalAlignment, get_aligned_position
from .font import Font, get_font, get_line_height, aligned_text, aligned_wrapped_text

_icon_cache: Dict[Tuple[str, Vector2Type], Image.Image] = {}


def get_icon(name: str, size: Optional[Vector2Type] = None) -> ImageFont.Image:
    size: Vector2Type = size or (32, 32)
    key = (name, size)

    if key in _icon_cache:
        return _icon_cache[key]

    stream = io.BytesIO()
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../../resources/icons/{name}.svg'))

    cairosvg.svg2png(url=path, write_to=stream, output_width=size[0], output_height=size[1])

    image = Image.open(stream)
    image.load()

    image = ImageOps.invert(image.getchannel('A')).convert('1')

    _icon_cache[key] = image

    return image


def draw_image(dest: Image.Image,
               source: Image.Image,
               area: Optional[Vector2Type] = None,
               offset: Optional[Vector2Type] = None,
               resize: bool = False,
               horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
               vertical_alignment: VerticalAlignment = VerticalAlignment.TOP,
               pre_processors: Optional[Iterable[Callable[[Image.Image], Image.Image]]] = None,
               post_processors: Optional[Iterable[Callable[[Image.Image], Image.Image]]] = None):
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

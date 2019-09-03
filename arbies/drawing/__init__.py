from __future__ import annotations
import os
import io
from PIL import Image, ImageFont, ImageOps
import cairosvg
from typing import Optional, Tuple, Dict
from ._consts import HorizontalAlignment, VerticalAlignment
from .font import Font, get_font, get_line_height, aligned_text, aligned_wrapped_text

Vector2Type = Tuple[float, float]

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

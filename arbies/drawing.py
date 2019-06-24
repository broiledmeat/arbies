import os
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
import cairosvg
from typing import Optional, Tuple, Dict

_font_cache: Dict[Tuple[str, int], ImageFont.ImageFont] = {}
_icon_cache: Dict[Tuple[str, Tuple[int, int]], Image.Image] = {}


def get_font(name: str = 'Roboto-Regular', size=14) -> ImageFont.ImageFont:
    key = (name, size)

    if key in _font_cache:
        return _font_cache[key]

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../resources/fonts/{name}.ttf'))
    font = ImageFont.truetype(path, size)

    _font_cache[key] = font

    return font


def get_icon(name: str, size: Optional[Tuple[int, int]] = None) -> ImageFont.Image:
    size: Tuple[int, int] = size or (32, 32)
    key = (name, size)

    if key in _icon_cache:
        return _icon_cache[key]

    stream = io.BytesIO()
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../resources/icons/{name}.svg'))

    cairosvg.svg2png(url=path, write_to=stream, output_width=size[0], output_height=size[1])

    image = Image.open(stream)
    image.load()

    image = ImageOps.invert(image.getchannel('A')).convert('1')

    _icon_cache[key] = image

    return image


def aligned_text(draw: ImageDraw.ImageDraw,
                 text: str,
                 position: Optional[Tuple[float, float]] = None,
                 rect: Optional[Tuple[float, float]] = None,
                 halign: str = 'left',
                 valign: str = 'top',
                 font: ImageFont.ImageFont = None):
    assert(position is not None or rect is not None)

    x, y = position or (0, 0)
    w, h = rect or (0, 0)
    tw, th = draw.textsize(text, font=font)

    if halign == 'left':
        pass
    elif halign == 'center':
        x = (w / 2) - (tw / 2)
    elif halign == 'right':
        x = w - tw
    else:
        raise ValueError(halign)

    if valign == 'top':
        pass
    elif valign == 'middle':
        y = (h / 2) - (th / 2)
    elif valign == 'bottom':
        y = h - th
    else:
        raise ValueError(valign)

    draw.text((x, y), text, font=font)

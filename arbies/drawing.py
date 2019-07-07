import os
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
import cairosvg
from typing import Optional, Tuple, List, Dict

Vector2 = Tuple[float, float]

_font_cache: Dict[Tuple[str, int], ImageFont.ImageFont] = {}
_icon_cache: Dict[Tuple[str, Vector2], Image.Image] = {}


def get_font(name: str = 'Roboto-Regular', size=14) -> ImageFont.ImageFont:
    key = (name, size)

    if key in _font_cache:
        return _font_cache[key]

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../resources/fonts/{name}.ttf'))
    font = ImageFont.truetype(path, size)

    _font_cache[key] = font

    return font


def get_icon(name: str, size: Optional[Vector2] = None) -> ImageFont.Image:
    size: Vector2 = size or (32, 32)
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
                 area: Vector2,
                 offset: Optional[Vector2] = None,
                 horizontal_alignment: str = 'left',
                 vertical_alignment: str = 'top',
                 font: ImageFont.ImageFont = None):
    size = draw.textsize(text, font=font)
    x, y = _get_aligned_position(size, area, horizontal_alignment, vertical_alignment)

    if offset is not None:
        x += offset[0]
        y += offset[1]

    draw.text((x, y), text, font=font)


def aligned_wrapped_text(draw: ImageDraw.ImageDraw,
                         text: str,
                         area: Vector2,
                         offset: Optional[Vector2] = None,
                         horizontal_alignment: str = 'left',
                         vertical_alignment: str = 'top',
                         font: ImageFont.ImageFont = None):
    sections: List[Tuple[str, Tuple[int, int]]] = []
    section: str = ''
    size: Tuple[int, int] = (0, 0)

    for token in text.split():
        if len(section) == 0:
            check = token
        else:
            check = section + ' ' + token
        check_size = draw.textsize(check, font=font)

        if len(section) > 0 and check_size[0] > area[0]:
            sections.append((section, size))
            section = token
            continue

        section = check
        size = check_size
    else:
        sections.append((section, size))

    if horizontal_alignment == 'left':
        x = 0
    elif horizontal_alignment == 'center':
        x = area[0] / 2
    elif horizontal_alignment == 'right':
        x = area[0]
    else:
        raise ValueError(horizontal_alignment)

    total_height = sum([x[1][1] for x in sections])
    if vertical_alignment == 'top':
        y = 0
    elif vertical_alignment == 'middle':
        y = (area[1] - total_height) / 2
    elif vertical_alignment == 'bottom':
        y = area[1] - total_height
    else:
        raise ValueError(vertical_alignment)

    if offset is not None:
        x += offset[0]
        y += offset[1]

    for section in sections:
        text: str = section[0]
        # noinspection PyTypeChecker
        size: Vector2 = section[1]

        x, _ = _get_aligned_position(size, area, horizontal_alignment, 'top')

        draw.text((x, y), text, font=font)

        y += section[1][1]


def _get_aligned_position(section: Vector2,
                          area: Vector2,
                          horizontal_alignment: str,
                          vertical_alignment: str
                          ) -> Vector2:
    if horizontal_alignment == 'left':
        x = 0
    elif horizontal_alignment == 'center':
        x = (area[0] - section[0]) / 2
    elif horizontal_alignment == 'right':
        x = area[0] - section[0]
    else:
        raise ValueError(horizontal_alignment)

    if vertical_alignment == 'top':
        y = 0
    elif vertical_alignment == 'middle':
        y = (area[1] - section[1]) / 2
    elif vertical_alignment == 'bottom':
        y = area[1] - section[1]
    else:
        raise ValueError(vertical_alignment)

    return x, y

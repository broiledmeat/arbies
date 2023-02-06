from __future__ import annotations
import os
from PIL import ImageDraw, ImageFont
from typing import TYPE_CHECKING, Union, Optional, Tuple, List, Dict
from ._consts import HorizontalAlignment, VerticalAlignment, get_aligned_position

if TYPE_CHECKING:
    from . import Vector2Type, ColorType
    from ..manager import ConfigDict


class Font(ImageFont.FreeTypeFont):
    _default_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                      '../../../resources/fonts/RobotoCondensed-Regular.ttf'))
    _default_size: int = 14
    _default_line_height: float = 1.2

    def __init__(self, path: Union[str, bytes], size: int = _default_size, line_height: float = _default_line_height):
        super().__init__(font=path, size=size)
        self.line_height: float = line_height

    def with_size(self, size: int) -> Font:
        if size == self.size:
            return self
        return Font(self.path, size=size, line_height=self.line_height)

    @classmethod
    def load_from_config(cls, name: str, config: ConfigDict) -> Font:
        global _default_font

        path = config.get('Path', Font._default_path)
        size = config.get('Size', Font._default_size)
        line_height = config.get('LineHeight', Font._default_line_height)

        if name is None or len(name) == 0:
            raise ValueError(f'Font name is either not defined or is blank.')

        if path is None or not os.path.isfile(path):
            raise ValueError(f'Font path "{path}" can not be found.')

        font = Font(path, size=size, line_height=line_height)
        _font_cache[name] = font

        if len(_font_cache) == 1:
            _default_font = font

        return font


AnyFontType = Union[ImageFont.ImageFont, ImageFont.FreeTypeFont, Font]

_default_font: Optional[Font] = None
_font_cache: Dict[str, Font] = {}


def _get_default_font() -> Font:
    global _default_font

    if _default_font is None:
        # noinspection PyProtectedMember
        _default_font = Font(Font._default_path)

    return _default_font


def get_font(name: Optional[str] = None, size: Optional[int] = None) -> Font:
    font: Font

    if name is not None:
        if name not in _font_cache:
            raise ValueError(f'No font named "{name}"')
        font = _font_cache[name]
    else:
        font = _get_default_font()

    if size is not None:
        return font.with_size(size)

    return font


def get_line_height(font: AnyFontType) -> float:
    if isinstance(font, Font):
        return font.getmetrics()[0] * font.line_height
    elif isinstance(font, ImageFont.FreeTypeFont):
        # noinspection PyProtectedMember
        return font.getmetrics()[0] * Font._default_line_height
    elif isinstance(font, ImageFont.ImageFont):
        return font.getsize('ABCDEFGHIJKLMNOPQRSTUVWXYZ')[1]
    raise TypeError(font)


def aligned_text(draw: ImageDraw.ImageDraw,
                 font: AnyFontType,
                 text: str,
                 fill: ColorType,
                 area: Vector2Type,
                 offset: Optional[Vector2Type] = None,
                 horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
                 vertical_alignment: VerticalAlignment = VerticalAlignment.TOP):
    size = draw.textsize(text, font=font)
    x, y = get_aligned_position(size, area, horizontal_alignment, vertical_alignment)

    if offset is not None:
        x += offset[0]
        y += offset[1]

    draw.text((x, y), text, font=font, fill=fill)


def aligned_wrapped_text(draw: ImageDraw.ImageDraw,
                         font: AnyFontType,
                         text: str,
                         fill: ColorType,
                         area: Vector2Type,
                         offset: Optional[Vector2Type] = None,
                         horizontal_alignment: HorizontalAlignment = HorizontalAlignment.LEFT,
                         vertical_alignment: VerticalAlignment = VerticalAlignment.TOP):
    line_height = get_line_height(font)
    sections: List[Tuple[str, Vector2Type]] = []
    section: str = ''
    section_size: Vector2Type = (0, 0)

    i: int = 0
    tokens: List[str] = text.split()
    while i < len(tokens):
        token = tokens[i]

        if len(section) == 0:
            check = token
        else:
            check = section + ' ' + token

        size = draw.textsize(check, font=font)

        if len(section) > 0 and size[0] > area[0]:
            sections.append((section, section_size))
            section = ''
            section_size = (0, 0)
            continue

        section = check
        section_size = size
        i += 1

        if i == len(tokens):
            sections.append((section, section_size))

    total_height = line_height * len(sections)

    if horizontal_alignment == HorizontalAlignment.LEFT:
        x = 0
    elif horizontal_alignment == HorizontalAlignment.CENTER:
        x = area[0] / 2
    elif horizontal_alignment == HorizontalAlignment.RIGHT:
        x = area[0]
    else:
        raise ValueError(horizontal_alignment)

    if vertical_alignment == VerticalAlignment.TOP:
        y = 0
    elif vertical_alignment == VerticalAlignment.CENTER:
        y = (area[1] - total_height) / 2
    elif vertical_alignment == VerticalAlignment.BOTTOM:
        y = area[1] - total_height
    else:
        raise ValueError(vertical_alignment)

    if offset is not None:
        x += offset[0]
        y += offset[1]

    for section in sections:
        text: str = section[0]
        # noinspection PyTypeChecker
        size: Vector2Type = section[1]

        x, _ = get_aligned_position(size, area, horizontal_alignment, VerticalAlignment.TOP)

        draw.text((x, y), text, font=font, fill=fill)

        y += line_height

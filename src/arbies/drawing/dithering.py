# Adapted from work by sloum. https://tildegit.org/sloum/lid

from PIL import Image, PyAccess
from typing import Callable

_PixelsType = PyAccess.PyAccess
_KernelType = Callable[[_PixelsType, _PixelsType, int, int], None]


def _run_kernel(source: Image.Image, kernel: _KernelType) -> Image.Image:
    source = source.copy().convert('L')
    dest = Image.new('1', source.size)
    width, height = source.size

    source_pixels: PyAccess.PyAccess = source.load()
    dest_pixels: PyAccess.PyAccess = dest.load()

    for row in range(0, height):
        for col in range(0, width):
            kernel(source_pixels, dest_pixels, col, row)

    return dest


def ordered_dither_4(source: Image.Image) -> Image.Image:
    dots = [[64, 128], [192, 0]]

    def kernel(src: _PixelsType, dest: _PixelsType, col: int, row: int):
        dot_row: int = 1 if row % 2 else 0
        dot_col: int = 1 if col % 2 else 0
        dest[col, row] = int(src[col, row] > dots[dot_row][dot_col])

    return _run_kernel(source, kernel)


def ordered_dither_9(source: Image.Image) -> Image.Image:
    dots = [[0, 196, 84], [168, 140, 56], [112, 28, 224]]

    def kernel(src: _PixelsType, dest: _PixelsType, col: int, row: int):
        dot_row: int = 0
        dot_col: int = 0

        if not row % 3:
            dot_row = 2
        elif not row % 2:
            dot_row = 1

        if not col % 3:
            dot_col = 2
        elif not col % 2:
            dot_col = 1

        dest[col, row] = int(src[col, row] > dots[dot_row][dot_col])

    return _run_kernel(source, kernel)


def threshold_dither(source: Image.Image, threshold: int | None = None) -> Image.Image:
    if threshold is None:
        pixels = list(source.convert('L').getdata())
        threshold = sum(pixels) // len(pixels)

    def kernel(src: _PixelsType, dest: _PixelsType, col: int, row: int):
        dest[col, row] = int(src[col, row] > threshold)

    return _run_kernel(source, kernel)


def random_dither(source: Image.Image) -> Image.Image:
    from random import randint

    def kernel(src: _PixelsType, dest: _PixelsType, col: int, row: int):
        dest[col, row] = int(src[col, row] > randint(1, 255))

    return _run_kernel(source, kernel)


def error_diffusion_dither(source: Image.Image) -> Image.Image:
    width, height = source.size
    mov = [[0, 1, 0.4375], [1, 1, 0.0625], [1, 0, 0.3125], [1, -1, 0.1875]]

    def kernel(src: _PixelsType, dest: _PixelsType, col: int, row: int):
        current: int = src[col, row]
        res: bool = current > 128
        diff: int = current - (255 if res else 0)

        for part in mov:
            if row + part[0] >= height or col + part[1] >= width or col + part[1] <= 0:
                continue
            p: int = src[col + part[1], row + part[0]]
            p = round(diff * part[2] + p)
            src[col + part[1], row + part[0]] = max(0, min(255, p))

        dest[col, row] = int(res)

    return _run_kernel(source, kernel)

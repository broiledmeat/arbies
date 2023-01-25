from __future__ import annotations
from typing import Union


class Vector2(tuple):
    def __init__(self, x: Union[int, Vector2] = 0, y: int = 0):
        pass

    def __new__(cls, x: Union[int, Vector2] = 0, y: int = 0):
        if isinstance(x, (tuple, list)):
            return super().__new__(cls, x)
        else:
            return super().__new__(cls, (x, y))

    @property
    def x(self) -> int:
        return self[0]

    @property
    def y(self) -> int:
        return self[1]


class Vector4(tuple):
    def __init__(self,
                 x: Union[int, Vector2] = 0,
                 y: int = 0,
                 w: int = 0,
                 z: int = 0):
        pass

    def __new__(cls,
                x: Union[int, Vector4] = 0,
                y: int = 0,
                w: int = 0,
                z: int = 0):
        if isinstance(x, (tuple, list)):
            return super().__new__(cls, x)
        else:
            return super().__new__(cls, (x, y, w, z))

    @property
    def x(self) -> int:
        return self[0]

    @property
    def y(self) -> int:
        return self[1]

    @property
    def w(self) -> int:
        return self[2]

    @property
    def z(self) -> int:
        return self[3]

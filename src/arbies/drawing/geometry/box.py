from __future__ import annotations
from .vector import Vector4


class Box(Vector4):
    def __init__(self, x: int = 0, y: int = 0, w: int = 0, z: int = 0):
        super().__init__(x, y, w, z)

    @property
    def width(self) -> int:
        return abs(self.w - self.x)

    @property
    def height(self) -> int:
        return abs(self.z - self.y)

    def intersects(self, other: Box) -> bool:
        return not (self.w < other.x or other.w < self.x or
                    self.z < other.y or other.z < self.y)

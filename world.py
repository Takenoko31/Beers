"""World helpers for toroidal geometry."""
from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class World:
    width: float = 1024.0
    height: float = 1024.0

    def wrap_scalar(self, d: float, length: float) -> float:
        return ((d + length / 2.0) % length) - length / 2.0

    def torus_delta(self, x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
        dx = self.wrap_scalar(x2 - x1, self.width)
        dy = self.wrap_scalar(y2 - y1, self.height)
        return dx, dy

    def torus_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        dx, dy = self.torus_delta(x1, y1, x2, y2)
        return math.hypot(dx, dy)

    def wrap_position(self, x: float, y: float) -> tuple[float, float]:
        return x % self.width, y % self.height

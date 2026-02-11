"""Uniform grid spatial hash for neighbor queries on torus."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple
import math

from creature import Creature
from world import World


@dataclass
class SpatialHash:
    world: World
    cell_size: float

    def __post_init__(self) -> None:
        self.cols = max(1, int(math.ceil(self.world.width / self.cell_size)))
        self.rows = max(1, int(math.ceil(self.world.height / self.cell_size)))
        self.cells: Dict[Tuple[int, int], List[Creature]] = defaultdict(list)

    def clear(self) -> None:
        self.cells.clear()

    def _key(self, x: float, y: float) -> tuple[int, int]:
        return int(x / self.cell_size) % self.cols, int(y / self.cell_size) % self.rows

    def insert(self, c: Creature) -> None:
        self.cells[self._key(c.x, c.y)].append(c)

    def rebuild(self, creatures: Iterable[Creature]) -> None:
        self.clear()
        for c in creatures:
            if not c.dead:
                self.insert(c)

    def query_radius(self, x: float, y: float, radius: float) -> list[Creature]:
        cx, cy = self._key(x, y)
        reach = int(math.ceil(radius / self.cell_size))
        out: list[Creature] = []
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                out.extend(self.cells.get(((cx + dx) % self.cols, (cy + dy) % self.rows), []))
        return out

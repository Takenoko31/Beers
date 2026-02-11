"""Terrain generation and slope utilities."""
from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass
class TerrainConfig:
    nx: int = 64
    ny: int = 64
    smoothing_passes: int = 4
    e0: float = 0.5
    c_mountain: float = 3.0


def _new_grid(nx: int, ny: int, val: float = 0.0) -> list[list[float]]:
    return [[val for _ in range(ny)] for _ in range(nx)]


def smooth_wrap(field: list[list[float]]) -> list[list[float]]:
    nx, ny = len(field), len(field[0])
    out = _new_grid(nx, ny)
    for i in range(nx):
        ip, im = (i + 1) % nx, (i - 1) % nx
        for j in range(ny):
            jp, jm = (j + 1) % ny, (j - 1) % ny
            out[i][j] = (field[i][j] + field[ip][j] + field[im][j] + field[i][jp] + field[i][jm]) / 5.0
    return out


def normalize(field: list[list[float]]) -> list[list[float]]:
    vals = [v for row in field for v in row]
    lo, hi = min(vals), max(vals)
    span = max(1e-8, hi - lo)
    return [[(v - lo) / span for v in row] for row in field]


def generate_elevation(cfg: TerrainConfig, rng: random.Random) -> list[list[float]]:
    elev = [[rng.random() for _ in range(cfg.ny)] for _ in range(cfg.nx)]
    for _ in range(cfg.smoothing_passes):
        elev = smooth_wrap(elev)
    return normalize(elev)


def productivity_from_elevation(elevation: list[list[float]], e0: float, c_mountain: float) -> list[list[float]]:
    out = []
    for row in elevation:
        r = []
        for e in row:
            p = 1.0 - c_mountain * (e - e0) ** 2
            r.append(max(0.0, min(1.0, p)))
        out.append(r)
    return out


def slope_magnitude(elevation: list[list[float]], i: int, j: int) -> float:
    nx, ny = len(elevation), len(elevation[0])
    ip, im = (i + 1) % nx, (i - 1) % nx
    jp, jm = (j + 1) % ny, (j - 1) % ny
    dx = 0.5 * (elevation[ip][j] - elevation[im][j])
    dy = 0.5 * (elevation[i][jp] - elevation[i][jm])
    return (dx * dx + dy * dy) ** 0.5

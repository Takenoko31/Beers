"""Nutrition field dynamics (logistic growth + diffusion)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NutritionConfig:
    r0: float = 0.02
    k0: float = 10.0
    k_min: float = 0.2
    diffusion: float = 0.12


class NutritionField:
    def __init__(self, productivity: list[list[float]], cfg: NutritionConfig):
        self.cfg = cfg
        self.productivity = productivity
        self.nx = len(productivity)
        self.ny = len(productivity[0])
        self.r = [[cfg.r0 * productivity[i][j] for j in range(self.ny)] for i in range(self.nx)]
        self.k = [[cfg.k0 * productivity[i][j] + cfg.k_min for j in range(self.ny)] for i in range(self.nx)]
        self.n = [[0.6 * self.k[i][j] for j in range(self.ny)] for i in range(self.nx)]

    def update(self) -> None:
        new_n = [[0.0 for _ in range(self.ny)] for _ in range(self.nx)]
        for i in range(self.nx):
            ip, im = (i + 1) % self.nx, (i - 1) % self.nx
            for j in range(self.ny):
                jp, jm = (j + 1) % self.ny, (j - 1) % self.ny
                nij = self.n[i][j]
                kij = max(self.k[i][j], 1e-8)
                growth = self.r[i][j] * nij * (1.0 - nij / kij)
                lap = self.n[ip][j] + self.n[im][j] + self.n[i][jp] + self.n[i][jm] - 4.0 * nij
                val = nij + growth + self.cfg.diffusion * lap
                if val < 0.0:
                    val = 0.0
                if val > self.k[i][j]:
                    val = self.k[i][j]
                new_n[i][j] = val
        self.n = new_n

    def inject_circle(self, cx: float, cy: float, radius_cells: float, delta: float) -> None:
        r2 = radius_cells * radius_cells
        for i in range(self.nx):
            di = min(abs(i - cx), self.nx - abs(i - cx))
            for j in range(self.ny):
                dj = min(abs(j - cy), self.ny - abs(j - cy))
                if di * di + dj * dj <= r2:
                    self.n[i][j] = min(self.k[i][j], max(0.0, self.n[i][j] + delta))

    def total_nutrition(self) -> float:
        return sum(sum(row) for row in self.n)

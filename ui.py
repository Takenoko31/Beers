"""Optional intervention helpers for god-like actions."""
from __future__ import annotations

import random


def inject_nutrition(sim, x: float, y: float, radius_cells: float, delta: float) -> None:
    sim.nutrition.inject_circle(x, y, radius_cells, delta)


def disease(sim, damage_factor: float = 0.5, fraction: float = 0.2) -> None:
    n = int(len(sim.creatures) * fraction)
    for c in random.sample(sim.creatures, k=max(0, min(n, len(sim.creatures)))):
        c.hp *= max(0.0, min(1.0, damage_factor))


def meteor(sim, x: float, y: float, radius: float, nutrition_delta: float = -1.0) -> None:
    for c in sim.creatures:
        dx, dy = sim.world.torus_delta(x, y, c.x, c.y)
        if dx * dx + dy * dy <= radius * radius:
            c.dead = True
    i = int(x / sim.world.width * sim.nutrition.nx)
    j = int(y / sim.world.height * sim.nutrition.ny)
    sim.nutrition.inject_circle(i, j, radius / (sim.world.width / sim.nutrition.nx), nutrition_delta)

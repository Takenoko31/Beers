"""Main simulation loop for EvoGarden v0.1."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import random

from behaviors import choose_velocity, feed_herbivore, local_density, predation, reproduction_phase, update_metabolism
from creature import Creature, Species, random_creature
from logging import SimLogger
from nutrition import NutritionConfig, NutritionField
from spatial_hash import SpatialHash
from terrain import TerrainConfig, generate_elevation, productivity_from_elevation
from world import World


@dataclass
class SimConfig:
    width: float = 1024
    height: float = 1024
    nx: int = 64
    ny: int = 64
    herbivores: int = 140
    carnivores: int = 40
    seed: int = 7


class Simulation:
    def __init__(self, cfg: SimConfig):
        self.cfg = cfg
        self.world = World(cfg.width, cfg.height)
        self.rng = random.Random(cfg.seed)
        terrain_cfg = TerrainConfig(nx=cfg.nx, ny=cfg.ny)
        self.elevation = generate_elevation(terrain_cfg, self.rng)
        self.productivity = productivity_from_elevation(self.elevation, terrain_cfg.e0, terrain_cfg.c_mountain)
        self.nutrition = NutritionField(self.productivity, NutritionConfig())

        self.params = {
            "eat_rate": 0.8,
            "eta_eat": 1.0,
            "bite_cost": 1.5,
            "cooldown_ticks": 12,
            "prey_energy_gain": 18.0,
            "basal_cost": 0.05,
            "move_cost": 0.02,
            "slope_cost": 0.06,
            "mature_age": 200,
            "mate_radius": 10.0,
            "gestation_ticks": 300,
            "mate_cooldown_ticks": 120,
            "male_mate_cost": 3.0,
            "female_mate_cost": 2.0,
            "birth_cost": 6.0,
            "male_mate_min": 8.0,
            "female_mate_min": 8.0,
            "rho0": 12.0,
            "a_mate": 0.08,
            "crowd_cost": 0.03,
        }

        self.creatures: list[Creature] = []
        for _ in range(cfg.herbivores):
            self.creatures.append(random_creature(Species.HERBIVORE, self.rng.uniform(0, cfg.width), self.rng.uniform(0, cfg.height), self.rng))
        for _ in range(cfg.carnivores):
            self.creatures.append(random_creature(Species.CARNIVORE, self.rng.uniform(0, cfg.width), self.rng.uniform(0, cfg.height), self.rng))

        self.spatial = SpatialHash(self.world, cell_size=80.0)
        self.tick = 0
        self.logger = SimLogger(interval=10)
        self.last_father = {}

    def cell_of(self, c: Creature) -> tuple[int, int]:
        nx, ny = self.nutrition.nx, self.nutrition.ny
        i = int(c.x / self.world.width * nx) % nx
        j = int(c.y / self.world.height * ny) % ny
        return i, j

    def step(self) -> None:
        self.tick += 1
        self.spatial.rebuild(self.creatures)
        for c in self.creatures:
            if not c.dead:
                c.density = local_density(c, self)
        for c in self.creatures:
            if c.dead:
                continue
            choose_velocity(c, self)
        for c in self.creatures:
            if c.dead:
                continue
            c.x, c.y = self.world.wrap_position(c.x + c.vx, c.y + c.vy)
            c.age += 1
            c.cooldown = max(0, c.cooldown - 1)
            c.mate_cooldown = max(0, c.mate_cooldown - 1)
        self.spatial.rebuild(self.creatures)

        for c in self.creatures:
            if not c.dead and c.species == Species.HERBIVORE:
                feed_herbivore(c, self)
        for c in self.creatures:
            if not c.dead and c.species == Species.CARNIVORE:
                predation(c, self)
        for c in self.creatures:
            if not c.dead:
                update_metabolism(c, self)
        births = reproduction_phase(self.creatures, self)
        self.creatures.extend(births)
        self.creatures = [c for c in self.creatures if not c.dead]
        self.nutrition.update()
        self.logger.maybe_log(self)

    def run(self, ticks: int) -> None:
        for _ in range(ticks):
            self.step()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EvoGarden simulation")
    parser.add_argument("--ticks", type=int, default=1000, help="Ticks for headless mode")
    parser.add_argument("--render", action="store_true", help="Launch futuristic Tkinter renderer")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--herbivores", type=int, default=140)
    parser.add_argument("--carnivores", type=int, default=40)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sim = Simulation(SimConfig(seed=args.seed, herbivores=args.herbivores, carnivores=args.carnivores))

    if args.render:
        from ui import FuturisticRenderer

        renderer = FuturisticRenderer(sim)
        renderer.run()
    else:
        sim.run(args.ticks)
        sim.logger.write_csv("outputs/sim_log.csv")
        print(f"done: tick={sim.tick}, creatures={len(sim.creatures)}")


if __name__ == "__main__":
    main()

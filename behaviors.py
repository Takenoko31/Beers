"""Behavior rules for herbivores and carnivores."""
from __future__ import annotations

import math
import random
from typing import Iterable

from creature import Creature, Genes, Sex, Species, random_creature
from world import World
from terrain import slope_magnitude


def _norm(vx: float, vy: float) -> tuple[float, float]:
    n = math.hypot(vx, vy)
    if n <= 1e-8:
        return 0.0, 0.0
    return vx / n, vy / n


def random_walk(c: Creature, rng: random.Random) -> tuple[float, float]:
    angle = rng.random() * math.tau
    return math.cos(angle), math.sin(angle)


def nutrition_gradient_dir(c: Creature, sim) -> tuple[float, float]:
    nx, ny = sim.nutrition.nx, sim.nutrition.ny
    i, j = sim.cell_of(c)
    best = sim.nutrition.n[i][j]
    best_dir = (0.0, 0.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ii, jj = (i + di) % nx, (j + dj) % ny
            val = sim.nutrition.n[ii][jj]
            if val > best:
                best = val
                best_dir = (float(di), float(dj))
    return _norm(*best_dir)


def choose_velocity(c: Creature, sim) -> None:
    hungry = c.energy < (6.0 if c.species == Species.HERBIVORE else 7.0)
    desired_x, desired_y = 0.0, 0.0

    if c.species == Species.HERBIVORE and hungry:
        desired_x, desired_y = nutrition_gradient_dir(c, sim)
    elif c.species == Species.CARNIVORE and hungry:
        target = nearest_prey(c, sim)
        if target is not None:
            dx, dy = sim.world.torus_delta(c.x, c.y, target.x, target.y)
            desired_x, desired_y = _norm(dx, dy)
    if desired_x == 0.0 and desired_y == 0.0:
        desired_x, desired_y = random_walk(c, sim.rng)

    c.vx = desired_x * c.speed()
    c.vy = desired_y * c.speed()


def nearest_prey(pred: Creature, sim) -> Creature | None:
    best = None
    best_d = float("inf")
    for other in sim.spatial.query_radius(pred.x, pred.y, pred.vision()):
        if other.dead or other.species != Species.HERBIVORE:
            continue
        d = sim.world.torus_distance(pred.x, pred.y, other.x, other.y)
        if d < best_d:
            best_d, best = d, other
    return best


def local_density(c: Creature, sim, radius: float = 40.0) -> float:
    count = 0
    for other in sim.spatial.query_radius(c.x, c.y, radius):
        if other.dead:
            continue
        if sim.world.torus_distance(c.x, c.y, other.x, other.y) <= radius:
            count += 1
    return float(max(0, count - 1))


def feed_herbivore(c: Creature, sim) -> None:
    i, j = sim.cell_of(c)
    eat = min(sim.nutrition.n[i][j], sim.params["eat_rate"] * c.size())
    sim.nutrition.n[i][j] -= eat
    c.energy += sim.params["eta_eat"] * float(eat)


def predation(pred: Creature, sim) -> None:
    if pred.cooldown > 0:
        return
    for prey in sim.spatial.query_radius(pred.x, pred.y, pred.radius() + 4.0):
        if prey.dead or prey.species != Species.HERBIVORE:
            continue
        d = sim.world.torus_distance(pred.x, pred.y, prey.x, prey.y)
        if d < pred.radius() + prey.radius():
            prey.hp -= pred.attack()
            pred.energy -= sim.params["bite_cost"]
            pred.cooldown = sim.params["cooldown_ticks"]
            if prey.hp <= 0:
                prey.dead = True
                pred.energy += sim.params["prey_energy_gain"]
            return


def update_metabolism(c: Creature, sim) -> None:
    basal = sim.params["basal_cost"] * c.metabolism_factor()
    move = sim.params["move_cost"] * math.hypot(c.vx, c.vy) * c.metabolism_factor()
    i, j = sim.cell_of(c)
    slope = slope_magnitude(sim.elevation, i, j)
    slope_c = sim.params["slope_cost"] * slope * math.hypot(c.vx, c.vy)
    crowd = sim.params["crowd_cost"] * max(0.0, c.density - sim.params["rho0"])
    c.energy -= basal + move + slope_c + crowd
    if c.energy < 0:
        c.hp += c.energy
    if c.hp <= 0:
        c.dead = True


def reproduction_phase(creatures: Iterable[Creature], sim) -> list[Creature]:
    births: list[Creature] = []
    females = [c for c in creatures if not c.dead and c.sex == Sex.FEMALE]
    males = [c for c in creatures if not c.dead and c.sex == Sex.MALE]

    for f in females:
        if f.pregnant:
            f.gestation_timer -= 1
            if f.gestation_timer <= 0 and f.energy > sim.params["birth_cost"]:
                f.energy -= sim.params["birth_cost"]
                f.pregnant = False
                child = spawn_child(f, sim)
                births.append(child)
        if f.dead or f.pregnant or f.age < sim.params["mature_age"]:
            continue
        if f.energy <= sim.params["female_mate_min"]:
            continue
        for m in males:
            if m.dead or m.age < sim.params["mature_age"]:
                continue
            if m.mate_cooldown > 0 or m.energy <= sim.params["male_mate_min"]:
                continue
            d = sim.world.torus_distance(f.x, f.y, m.x, m.y)
            if d > sim.params["mate_radius"]:
                continue
            p_mate = math.exp(-sim.params["a_mate"] * max(0.0, f.density - sim.params["rho0"]))
            if sim.rng.random() > p_mate:
                break
            f.pregnant = True
            f.gestation_timer = sim.params["gestation_ticks"]
            f.energy -= sim.params["female_mate_cost"]
            m.energy -= sim.params["male_mate_cost"]
            m.mate_cooldown = sim.params["mate_cooldown_ticks"]
            sim.last_father[f.id] = m
            break

    return births


def spawn_child(mother: Creature, sim) -> Creature:
    father = sim.last_father.get(mother.id)
    if father is None or father.dead:
        father = mother
    genes = crossover(mother.genes, father.genes, sim.rng)
    sex = Sex.FEMALE if sim.rng.random() < 0.5 else Sex.MALE
    child = random_creature(mother.species, mother.x + sim.rng.uniform(-2, 2), mother.y + sim.rng.uniform(-2, 2), sim.rng)
    child.sex = sex
    child.genes = genes
    child.hp *= child.hp_factor()
    child.energy = 5.0
    child.age = 0
    return child


def crossover(mg: Genes, fg: Genes, rng: random.Random) -> Genes:
    out = []
    for mv, fv in zip(mg.__dict__.values(), fg.__dict__.values()):
        a = rng.random()
        g = (1.0 - a) * mv + a * fv
        if rng.random() < 0.02:
            g += rng.gauss(0.0, 0.03)
        out.append(max(0.0, min(1.0, g)))
    return Genes(*out)

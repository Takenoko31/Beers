"""Creature state and genotype/phenotype mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import count
import math
import random


class Species(str, Enum):
    HERBIVORE = "H"
    CARNIVORE = "C"


class Sex(str, Enum):
    FEMALE = "F"
    MALE = "M"


_id_gen = count(1)


@dataclass
class Genes:
    g_speed: float
    g_vision: float
    g_attack: float
    g_repro: float
    g_size: float

    @staticmethod
    def random(rng: random.Random) -> "Genes":
        return Genes(*(rng.random() for _ in range(5)))


@dataclass
class Creature:
    species: Species
    sex: Sex
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    age: int = 0
    hp: float = 20.0
    energy: float = 10.0
    cooldown: int = 0
    mate_cooldown: int = 0
    pregnant: bool = False
    gestation_timer: int = 0
    genes: Genes = field(default_factory=lambda: Genes(0.5, 0.5, 0.5, 0.5, 0.5))
    dead: bool = False
    density: float = 0.0
    id: int = field(default_factory=lambda: next(_id_gen))

    def speed(self) -> float:
        base = map01(self.genes.g_speed, 0.8, 3.4)
        sex_factor = 1.05 if self.sex == Sex.MALE else 0.95
        return base * sex_factor

    def vision(self) -> float:
        base = map01(self.genes.g_vision, 20.0, 80.0)
        return base

    def attack(self) -> float:
        if self.species == Species.HERBIVORE:
            return 0.0
        base = map01(self.genes.g_attack, 2.0, 8.0)
        sex_factor = 1.1 if self.sex == Sex.MALE else 0.9
        return base * sex_factor

    def size(self) -> float:
        return map01(self.genes.g_size, 0.7, 1.6)

    def metabolism_factor(self) -> float:
        return 1.1 if self.sex == Sex.MALE else 0.95

    def hp_factor(self) -> float:
        return 0.95 if self.sex == Sex.MALE else 1.05

    def repro_threshold(self) -> float:
        return 8.0 / map01(self.genes.g_repro, 0.7, 1.3)

    def radius(self) -> float:
        return 2.2 * self.size()


def map01(g: float, lo: float, hi: float) -> float:
    return lo + max(0.0, min(1.0, g)) * (hi - lo)


def random_creature(species: Species, x: float, y: float, rng: random.Random) -> Creature:
    sex = Sex.FEMALE if rng.random() < 0.5 else Sex.MALE
    base_hp = 20.0 if species == Species.HERBIVORE else 28.0
    base_energy = 10.0 if species == Species.HERBIVORE else 12.0
    c = Creature(species=species, sex=sex, x=x, y=y, hp=base_hp, energy=base_energy, genes=Genes.random(rng))
    c.hp *= c.hp_factor()
    angle = rng.random() * 2.0 * math.pi
    v = c.speed() * 0.2
    c.vx, c.vy = v * math.cos(angle), v * math.sin(angle)
    return c

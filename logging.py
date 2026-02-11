"""Simulation logging utilities."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from creature import Species, Sex


@dataclass
class SimLogger:
    interval: int = 10
    rows: list[dict] = field(default_factory=list)
    extinction_events: list[tuple[int, str]] = field(default_factory=list)

    def maybe_log(self, sim) -> None:
        if sim.tick % self.interval != 0:
            return
        row = {
            "tick": sim.tick,
            "H_F": 0,
            "H_M": 0,
            "C_F": 0,
            "C_M": 0,
            "sum_nutrition": sim.nutrition.total_nutrition(),
            "H_g_speed": 0.0,
            "C_g_speed": 0.0,
            "H_g_vision": 0.0,
            "C_g_vision": 0.0,
            "H_g_repro": 0.0,
            "C_g_repro": 0.0,
        }
        hgenes, cgenes, hc, cc = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0, 0
        for c in sim.creatures:
            key = f"{c.species.value}_{c.sex.value}"
            row[key] += 1
            if c.species == Species.HERBIVORE:
                hc += 1
                hgenes[0] += c.genes.g_speed
                hgenes[1] += c.genes.g_vision
                hgenes[2] += c.genes.g_repro
            else:
                cc += 1
                cgenes[0] += c.genes.g_speed
                cgenes[1] += c.genes.g_vision
                cgenes[2] += c.genes.g_repro
        if hc:
            row["H_g_speed"], row["H_g_vision"], row["H_g_repro"] = [v / hc for v in hgenes]
        if cc:
            row["C_g_speed"], row["C_g_vision"], row["C_g_repro"] = [v / cc for v in cgenes]
        self.rows.append(row)

        if row["H_F"] + row["H_M"] == 0:
            self.extinction_events.append((sim.tick, "herbivore"))
        if row["C_F"] + row["C_M"] == 0:
            self.extinction_events.append((sim.tick, "carnivore"))

    def write_csv(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not self.rows:
            return
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.rows[0].keys()))
            writer.writeheader()
            writer.writerows(self.rows)

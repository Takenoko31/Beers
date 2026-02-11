"""UI and intervention helpers for god-like actions."""
from __future__ import annotations

import math
import random
import tkinter as tk

from creature import Species


# -------- God interventions --------
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


# -------- Futuristic renderer --------
class FuturisticRenderer:
    """Neon-like Tkinter renderer for EvoGarden."""

    def __init__(self, sim, width: int = 1100, height: int = 780, steps_per_frame: int = 2):
        self.sim = sim
        self.width = width
        self.height = height
        self.steps_per_frame = steps_per_frame

        self.root = tk.Tk()
        self.root.title("EvoGarden v0.1 // Neon Observatory")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#050816", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.running = True
        self.show_overlay = True

        self.colors = {
            "bg_grid": "#11213f",
            "text_main": "#d4f8ff",
            "text_sub": "#8ed6ff",
            "nutrition": "#00ffc8",
            "terrain": "#20174f",
            "herb": "#7dff83",
            "carn": "#ff5aa5",
            "herb_glow": "#00ff88",
            "carn_glow": "#ff2aa1",
            "panel": "#0d1633",
            "panel_border": "#2f65ff",
        }

        self.world_view_h = int(self.height * 0.78)
        self.panel_y = self.world_view_h

        self.root.bind("<space>", self._toggle_pause)
        self.root.bind("<Escape>", self._quit)
        self.root.bind("<h>", self._toggle_overlay)
        self.root.bind("<n>", self._inject_random_nutrition)
        self.root.bind("<m>", self._meteor_event)
        self.root.bind("<d>", self._disease_event)

    def _toggle_pause(self, _event=None) -> None:
        self.running = not self.running

    def _toggle_overlay(self, _event=None) -> None:
        self.show_overlay = not self.show_overlay

    def _quit(self, _event=None) -> None:
        self.root.destroy()

    def _inject_random_nutrition(self, _event=None) -> None:
        i = random.uniform(0, self.sim.nutrition.nx - 1)
        j = random.uniform(0, self.sim.nutrition.ny - 1)
        inject_nutrition(self.sim, i, j, radius_cells=4.0, delta=2.0)

    def _meteor_event(self, _event=None) -> None:
        x = random.uniform(0.0, self.sim.world.width)
        y = random.uniform(0.0, self.sim.world.height)
        meteor(self.sim, x, y, radius=30.0, nutrition_delta=-0.8)

    def _disease_event(self, _event=None) -> None:
        disease(self.sim, damage_factor=0.65, fraction=0.18)

    def _world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        sx = x / self.sim.world.width * self.width
        sy = y / self.sim.world.height * self.world_view_h
        return sx, sy

    def _draw_background(self) -> None:
        self.canvas.create_rectangle(0, 0, self.width, self.world_view_h, fill="#06091a", outline="")

        # Cyber grid lines
        grid = 55
        for x in range(0, self.width, grid):
            alpha_shift = (x // grid) % 3
            color = ["#0c1a39", "#112149", "#0a1733"][alpha_shift]
            self.canvas.create_line(x, 0, x, self.world_view_h, fill=color)
        for y in range(0, self.world_view_h, grid):
            alpha_shift = (y // grid) % 3
            color = ["#0c1a39", "#112149", "#0a1733"][alpha_shift]
            self.canvas.create_line(0, y, self.width, y, fill=color)

    def _draw_field(self) -> None:
        """Render low-res nutrition/terrain blocks for a holographic feel."""
        nx, ny = self.sim.nutrition.nx, self.sim.nutrition.ny
        step = max(2, nx // 32)
        cell_w = self.width / nx
        cell_h = self.world_view_h / ny

        for i in range(0, nx, step):
            for j in range(0, ny, step):
                n = self.sim.nutrition.n[i][j] / max(1e-6, self.sim.nutrition.k[i][j])
                e = self.sim.elevation[i][j]
                glow = int(25 + 180 * n)
                terrain = int(25 + 70 * e)
                color = f"#{terrain:02x}{glow:02x}{min(255, terrain + 80):02x}"
                x0 = i * cell_w
                y0 = j * cell_h
                x1 = (i + step) * cell_w
                y1 = (j + step) * cell_h
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

    def _draw_creatures(self) -> None:
        for c in self.sim.creatures:
            sx, sy = self._world_to_screen(c.x, c.y)
            r = max(2.0, c.radius() * 0.8)
            if c.species == Species.HERBIVORE:
                glow_col = self.colors["herb_glow"]
                core_col = self.colors["herb"]
            else:
                glow_col = self.colors["carn_glow"]
                core_col = self.colors["carn"]

            # faux glow layers
            self.canvas.create_oval(sx - r * 2.6, sy - r * 2.6, sx + r * 2.6, sy + r * 2.6, fill=glow_col, outline="")
            self.canvas.create_oval(sx - r * 1.6, sy - r * 1.6, sx + r * 1.6, sy + r * 1.6, fill=glow_col, outline="")
            self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=core_col, outline="#f6ffff", width=1)

            # heading vector
            speed = math.hypot(c.vx, c.vy)
            if speed > 1e-8:
                hx = sx + (c.vx / speed) * r * 2.5
                hy = sy + (c.vy / speed) * r * 2.5
                self.canvas.create_line(sx, sy, hx, hy, fill="#cfffff", width=1)

    def _draw_panel(self) -> None:
        self.canvas.create_rectangle(
            0,
            self.panel_y,
            self.width,
            self.height,
            fill=self.colors["panel"],
            outline=self.colors["panel_border"],
            width=2,
        )

        hf = sum(1 for c in self.sim.creatures if c.species == Species.HERBIVORE and c.sex.value == "F")
        hm = sum(1 for c in self.sim.creatures if c.species == Species.HERBIVORE and c.sex.value == "M")
        cf = sum(1 for c in self.sim.creatures if c.species == Species.CARNIVORE and c.sex.value == "F")
        cm = sum(1 for c in self.sim.creatures if c.species == Species.CARNIVORE and c.sex.value == "M")
        total_n = self.sim.nutrition.total_nutrition()

        line1 = f"TICK {self.sim.tick:06d}  |  HERB F/M: {hf}/{hm}  |  CARN F/M: {cf}/{cm}"
        line2 = f"NUTRITION Σ: {total_n:,.1f}  |  SPACE:PAUSE  H:HUD  N:INJECT  M:METEOR  D:DISEASE  ESC:QUIT"

        self.canvas.create_text(20, self.panel_y + 26, anchor="w", text=line1, fill=self.colors["text_main"], font=("Consolas", 14, "bold"))
        self.canvas.create_text(20, self.panel_y + 56, anchor="w", text=line2, fill=self.colors["text_sub"], font=("Consolas", 11))

    def _draw_overlay(self) -> None:
        if not self.show_overlay:
            return
        self.canvas.create_text(
            self.width - 20,
            20,
            anchor="ne",
            text="EvoGarden // Neon Observatory",
            fill="#9ad5ff",
            font=("Consolas", 12, "bold"),
        )

    def draw_frame(self) -> None:
        self.canvas.delete("all")
        self._draw_background()
        self._draw_field()
        self._draw_creatures()
        self._draw_panel()
        self._draw_overlay()

    def tick(self) -> None:
        if self.running:
            for _ in range(self.steps_per_frame):
                self.sim.step()
        self.draw_frame()
        self.root.after(33, self.tick)

    def run(self) -> None:
        self.tick()
        self.root.mainloop()

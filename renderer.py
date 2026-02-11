"""Tkinter-based near-future visualization for EvoGarden."""
from __future__ import annotations

import math
import tkinter as tk

from creature import Species


class EvoRenderer:
    def __init__(self, sim, width: int = 1200, height: int = 900, tick_per_frame: int = 2):
        self.sim = sim
        self.width = width
        self.height = height
        self.tick_per_frame = max(1, tick_per_frame)

        self.root = tk.Tk()
        self.root.title("EvoGarden // Neo-Bio Observatory")
        self.root.configure(bg="#030712")

        self.canvas = tk.Canvas(
            self.root,
            width=self.width,
            height=self.height,
            bg="#020617",
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.running = True
        self.root.bind("<space>", self._toggle_pause)
        self.root.bind("<Escape>", self._quit)
        self.root.bind("<q>", self._quit)

        self.cell_w = self.width / self.sim.nutrition.nx
        self.cell_h = self.height / self.sim.nutrition.ny
        self.last_tick = -1

    def _toggle_pause(self, _event=None):
        self.running = not self.running

    def _quit(self, _event=None):
        self.root.destroy()

    def color_for_nutrition(self, val: float, k: float) -> str:
        ratio = 0.0 if k <= 1e-8 else max(0.0, min(1.0, val / k))
        # cyber neon gradient: deep navy -> electric blue -> toxic lime
        r = int(10 + ratio * 40)
        g = int(20 + ratio * 220)
        b = int(35 + ratio * 230)
        return f"#{r:02x}{g:02x}{b:02x}"

    def draw_background(self):
        self.canvas.delete("all")
        step = 2
        for i in range(0, self.sim.nutrition.nx, step):
            x0 = i * self.cell_w
            x1 = min(self.width, (i + step) * self.cell_w)
            for j in range(0, self.sim.nutrition.ny, step):
                y0 = j * self.cell_h
                y1 = min(self.height, (j + step) * self.cell_h)
                n = self.sim.nutrition.n[i][j]
                k = self.sim.nutrition.k[i][j]
                c = self.color_for_nutrition(n, k)
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=c, outline="")

        # holographic grid overlay
        grid_color = "#0b1225"
        for gx in range(0, self.width, 60):
            self.canvas.create_line(gx, 0, gx, self.height, fill=grid_color)
        for gy in range(0, self.height, 60):
            self.canvas.create_line(0, gy, self.width, gy, fill=grid_color)

    def draw_creatures(self):
        sx = self.width / self.sim.world.width
        sy = self.height / self.sim.world.height
        for c in self.sim.creatures:
            x = c.x * sx
            y = c.y * sy
            rad = max(2.0, c.radius() * 0.9)
            if c.species == Species.HERBIVORE:
                fill = "#7CFFB2" if c.sex.value == "F" else "#33FFC7"
                glow = "#00ff99"
            else:
                fill = "#FF79C6" if c.sex.value == "F" else "#FF2E88"
                glow = "#ff3ea5"
            self.canvas.create_oval(x - rad - 1, y - rad - 1, x + rad + 1, y + rad + 1, outline=glow)
            self.canvas.create_oval(x - rad, y - rad, x + rad, y + rad, fill=fill, outline="")

    def draw_hud(self):
        hf = sum(1 for c in self.sim.creatures if c.species == Species.HERBIVORE and c.sex.value == "F")
        hm = sum(1 for c in self.sim.creatures if c.species == Species.HERBIVORE and c.sex.value == "M")
        cf = sum(1 for c in self.sim.creatures if c.species == Species.CARNIVORE and c.sex.value == "F")
        cm = sum(1 for c in self.sim.creatures if c.species == Species.CARNIVORE and c.sex.value == "M")
        txt = (
            f"TICK {self.sim.tick:05d}  //  HERB(F/M): {hf}/{hm}  //  CARN(F/M): {cf}/{cm}  //  "
            f"NUTRITION Σ: {self.sim.nutrition.total_nutrition():.1f}"
        )
        self.canvas.create_rectangle(10, 10, self.width - 10, 46, fill="#020b1e", outline="#1d4ed8")
        self.canvas.create_text(20, 28, anchor="w", text=txt, fill="#93c5fd", font=("Consolas", 13, "bold"))

        hint = "[SPACE] pause/resume  [Q/ESC] quit"
        self.canvas.create_text(self.width - 16, self.height - 16, anchor="e", text=hint, fill="#64748b", font=("Consolas", 11))

    def frame(self):
        if self.running:
            for _ in range(self.tick_per_frame):
                self.sim.step()

        if self.sim.tick != self.last_tick:
            self.last_tick = self.sim.tick
            self.draw_background()
            self.draw_creatures()
            self.draw_hud()

        self.root.after(16, self.frame)

    def run(self):
        self.frame()
        self.root.mainloop()

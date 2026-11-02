"""One reusable Canvas, time-proportional coordinates, no interpolation over gaps."""

import tkinter as tk
from datetime import timedelta
from app.ui import theme as t
from app.ui.enhancement_data import chart_points


class TemperatureChart(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, height=175, bg=t.PANEL, highlightthickness=0)
        self.points = ()
        self.unit = "°C"
        self.bind("<Configure>", lambda e: self.redraw())

    def set_data(self, rows, unit, timezone):
        self.points = chart_points(rows, unit, timezone)
        self.unit = unit
        self.redraw()

    def redraw(self):
        self.delete("all")
        self.configure(bg=t.PANEL)
        w, h = self.winfo_width(), self.winfo_height()
        valid = [v for _, v, _ in self.points if v is not None]
        if not valid:
            self.create_text(
                max(w / 2, 100),
                h / 2,
                text="Hourly temperatures unavailable",
                fill=t.MUTED,
            )
            return
        low, high = min(valid) - 1, max(valid) + 1
        for value in (low, (low + high) / 2, high):
            y = h - 40 - (value - low) / (high - low) * (h - 65)
            self.create_line(65, y, w - 22, y, fill="#54545b", dash=(2, 4))
            self.create_text(
                58, y, text=f"{value:.0f}{self.unit}", anchor="e", fill=t.MUTED
            )
        start = self.points[0][0]
        duration = max(3600, (self.points[-1][0] - start).total_seconds())
        previous = None
        for index, (stamp, value, label) in enumerate(self.points):
            x = 65 + (stamp - start).total_seconds() / duration * max(1, w - 125)
            if value is None:
                previous = None
                self.create_text(x, h / 2, text="—", fill=t.MUTED)
            else:
                y = h - 40 - (value - low) / (high - low) * (h - 65)
                if previous and stamp - previous[0] == timedelta(hours=1):
                    self.create_line(
                        previous[1],
                        previous[2],
                        x,
                        y,
                        fill=t.SELECTED,
                        width=2,
                        tags="segment",
                    )
                self.create_oval(
                    x - 4,
                    y - 4,
                    x + 4,
                    y + 4,
                    fill=t.SELECTED,
                    outline=t.TEXT,
                    tags="point",
                )
                self.create_text(x, y - 12, text=f"{value:.0f}°", fill=t.TEXT)
                previous = (stamp, x, y)
            self.create_text(
                x,
                h - 19,
                text=label[:12] + "\n" + label[13:],
                fill=t.MUTED,
                font=("Arial", 9),
            )

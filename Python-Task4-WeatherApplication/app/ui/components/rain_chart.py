import tkinter as tk
from zoneinfo import ZoneInfo
from app.ui import theme as t


class RainChart(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, bg=t.BG, highlightthickness=0, height=207, width=240)
        self.rows = ()
        self.timezone = "UTC"
        self.message = "Search a city"
        self.bind("<Configure>", lambda e: self.redraw())

    def set_data(self, rows=(), timezone="UTC", message="Forecast unavailable"):
        self.rows = rows
        self.timezone = timezone
        self.message = message
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50:
            return
        if not self.rows:
            self.create_text(
                w / 2,
                h / 2,
                text=self.message,
                fill=t.MUTED,
                font=("Arial", 12),
                width=w - 20,
            )
            return
        top, bottom, left, right = 22, h - 34, 42, w - 12
        for pct in (0, 50, 100):
            y = bottom - (bottom - top) * pct / 100
            self.create_line(left, y, right, y, fill="#303036", dash=(2, 3))
            self.create_text(
                left - 5,
                y,
                text=f"{pct}%",
                fill=t.MUTED,
                anchor="e",
                font=("Arial", 10),
            )
        step = (right - left) / 6
        for i, row in enumerate(self.rows):
            x = left + step * (i + 0.5)
            value = row.precipitation_probability
            y = bottom if value is None else bottom - (bottom - top) * value / 100
            if value is not None:
                self.create_line(
                    x,
                    bottom,
                    x,
                    max(top, y),
                    fill=t.SELECTED,
                    width=7,
                    capstyle=tk.ROUND,
                )
                if value == 0:
                    self.create_oval(
                        x - 3,
                        bottom - 3,
                        x + 3,
                        bottom + 3,
                        fill=t.SELECTED,
                        outline="",
                    )
            self.create_text(
                x,
                max(top - 10, y - 12),
                text="—" if value is None else f"{value:g}%",
                fill=t.TEXT,
                font=("Arial", 10),
            )
            self.create_text(
                x,
                bottom + 18,
                text=row.forecast_at.astimezone(ZoneInfo(self.timezone)).strftime(
                    "%Hh"
                ),
                fill=t.MUTED,
                font=("Arial", 10),
            )

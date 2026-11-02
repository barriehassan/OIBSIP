from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk
from app.ui import theme as t
from .weather_icon import original_icon
from app.ui.presentation import map_rectangle, project

ASSET = Path(__file__).resolve().parents[3] / "assets/maps/world_land.png"


class GlobalMap(tk.Canvas):
    def __init__(self, parent, select):
        super().__init__(parent, bg=t.MAP, highlightthickness=0, height=302)
        self.select = select
        self.markers = []
        self.active = None
        self.photo = None
        try:
            with Image.open(ASSET) as source:
                self.base = source.convert("RGB")
        except OSError:
            self.base = None
        self.bind("<Configure>", lambda e: self.redraw())

    def set_markers(self, markers, active):
        self.markers = markers
        self.active = active
        self.redraw()

    def redraw(self):
        self.delete("all")
        self.marker_images = []
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            return
        rect = map_rectangle(w, h)
        if self.base is None:
            self.create_text(
                w / 2,
                32,
                text="Map asset unavailable · locations listed below",
                fill=t.MUTED,
            )
            for i, (location, _) in enumerate(self.markers):
                self.create_text(
                    20,
                    65 + i * 30,
                    anchor="w",
                    text=f"{location.name}  {location.latitude:.2f}, {location.longitude:.2f}",
                    fill=t.TEXT,
                )
            return
        x0, y0, mw, mh = rect
        self.photo = ImageTk.PhotoImage(
            self.base.resize(
                (max(1, int(mw)), max(1, int(mh))), Image.Resampling.LANCZOS
            )
        )
        self.create_image(x0, y0, image=self.photo, anchor="nw")
        for i, (location, weather) in enumerate(self.markers):
            x, y = project(location.latitude, location.longitude, rect)
            tag = f"pin{i}"
            active = location == self.active
            self.create_oval(
                x - 10,
                y - 10,
                x + 10,
                y + 10,
                fill=t.BG,
                outline=t.SELECTED if active else "#74747b",
                width=2,
                tags=tag,
            )
            if weather:
                icon = ImageTk.PhotoImage(
                    original_icon(weather.current.icon_id).resize(
                        (24, 24), Image.Resampling.LANCZOS
                    )
                )
                self.marker_images.append(icon)
                self.create_image(x, y, image=icon, tags=tag)
            else:
                self.create_oval(
                    x - 3, y - 3, x + 3, y + 3, fill=t.MUTED, outline="", tags=tag
                )
            self.tag_bind(tag, "<Button-1>", lambda e, l=location: self.select(l))
            self.tag_bind(tag, "<Enter>", lambda e: self.configure(cursor="hand2"))
            self.tag_bind(tag, "<Leave>", lambda e: self.configure(cursor=""))
            if active:
                self.create_text(
                    min(max(x, 75), w - 75),
                    max(18, y - 23),
                    text=location.name,
                    fill=t.TEXT,
                    font=("Arial", 12, "bold"),
                )
        self.create_text(
            16,
            h - 16,
            text=(
                "Location overview · weather only for fetched places"
                if self.markers
                else "Search a city to place a marker"
            ),
            anchor="w",
            fill=t.MUTED,
            font=("Arial", 11),
        )

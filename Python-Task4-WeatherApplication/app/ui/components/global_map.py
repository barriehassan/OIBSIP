from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk
from app.ui import theme as t
from .weather_icon import original_icon
from app.ui.presentation import project
import customtkinter as ctk
from .chrome import symbol

ASSET = Path(__file__).resolve().parents[3] / "assets/maps/world_land.png"


class GlobalMap(tk.Canvas):
    def __init__(self, parent, select, explore=None):
        super().__init__(parent, bg=t.MAP, highlightthickness=0, height=302)
        self.select = select
        self.markers = []
        self.active = None
        self.photo = None
        self.zoom = 1.0
        self.center = (10.0, 18.0)
        self.show_markers = True
        self.drag = None
        self.controls = {}
        for name, command in (
            ("reset", self.reset),
            ("layers", self.toggle_markers),
            ("plus", lambda: self.change_zoom(1.35)),
            ("minus", lambda: self.change_zoom(1 / 1.35)),
            ("locate", self.recenter),
        ):
            button = t.button(
                self,
                "",
                command,
                width=32,
                height=32,
                fg_color="#353537",
                image=symbol(name, "#f5f5f7", 17),
            )
            self.controls[name] = button
        self.controls["reset"].place(x=10, y=10)
        self.controls["layers"].place(relx=1, x=-10, y=10, anchor="ne")
        self.controls["plus"].place(relx=1, rely=0.47, x=-10, anchor="e")
        self.controls["minus"].place(relx=1, rely=0.61, x=-10, anchor="e")
        self.controls["locate"].place(relx=1, rely=1, x=-10, y=-10, anchor="se")
        self.exploration = ctk.CTkFrame(
            self, width=190, height=188, fg_color="#fffffc", corner_radius=25
        )
        self.exploration.place(x=12, rely=1, y=-12, anchor="sw")
        self.exploration.pack_propagate(False)
        t.label(
            self.exploration,
            "Explore the global map\nand weather for your\nselected locations",
            size=12,
            color="#14151b",
            height=50,
        ).pack(pady=(10, 8))
        try:
            with Image.open(ASSET.with_name("storm_thumbnail.png")) as source:
                preview = ctk.CTkImage(
                    light_image=source.copy(), dark_image=source.copy(), size=(150, 52)
                )
        except OSError:
            preview = None
        ctk.CTkLabel(self.exploration, text="", image=preview, height=52).pack()
        t.button(
            self.exploration,
            "Get started",
            explore or self.reset,
            width=150,
            height=26,
            fg_color=t.LAVENDER,
            text_color="#14151b",
        ).pack(pady=10)
        self.bind("<ButtonPress-1>", self.start_pan)
        self.bind("<B1-Motion>", self.pan)
        self.bind("<ButtonRelease-1>", lambda e: setattr(self, "drag", None))
        try:
            with Image.open(ASSET) as source:
                self.base = source.convert("RGB")
        except OSError:
            self.base = None
        self.bind("<Configure>", lambda e: self.redraw())

    def reset(self):
        self.zoom = 1.0
        self.center = (10.0, 18.0)
        self.redraw()

    def change_zoom(self, factor):
        self.zoom = min(4.0, max(1.0, self.zoom * factor))
        self.redraw()

    def toggle_markers(self):
        self.show_markers = not self.show_markers
        self.controls["layers"].configure(
            fg_color="#353537" if self.show_markers else "#665983"
        )
        self.redraw()

    def recenter(self):
        if self.active:
            self.center = (self.active.longitude, self.active.latitude)
            self.zoom = max(1.8, self.zoom)
            self.redraw()

    def start_pan(self, event):
        self.drag = (event.x, event.y, self.center)

    def pan(self, event):
        if self.drag and self.base is not None:
            x, y, center = self.drag
            _, _, width, height = self.viewport()
            self.center = (
                center[0] - (event.x - x) / width * 360,
                center[1] + (event.y - y) / height * 180,
            )
            self.redraw()

    def viewport(self):
        """Cover the viewport without stretching; share the transform with pins."""
        w, h = self.winfo_width(), self.winfo_height()
        mw = max(w, 2 * h) * self.zoom
        mh = mw / 2
        lon, lat = self.center
        x = min(0, max(w - mw, w / 2 - (lon + 180) / 360 * mw))
        y = min(0, max(h - mh, h / 2 - (90 - lat) / 180 * mh))
        return x, y, mw, mh

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
        rect = self.viewport()
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
                    fill="#f5f5f7",
                )
            return
        x0, y0, mw, mh = rect
        self.photo = ImageTk.PhotoImage(
            self.base.resize(
                (max(1, int(mw)), max(1, int(mh))), Image.Resampling.LANCZOS
            )
        )
        self.create_image(x0, y0, image=self.photo, anchor="nw")
        for i, (location, weather) in enumerate(
            self.markers if self.show_markers else []
        ):
            x, y = project(location.latitude, location.longitude, rect)
            tag = f"pin{i}"
            active = location == self.active
            self.create_oval(
                x - 10,
                y - 10,
                x + 10,
                y + 10,
                fill="#111015",
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
            if 0 <= x <= w and 0 <= y <= h:
                self.create_text(
                    min(max(x + 15, 4), w - 82),
                    y,
                    anchor="w",
                    text=location.name,
                    fill="#f5f5f7",
                    font=("Arial", 12, "bold"),
                )

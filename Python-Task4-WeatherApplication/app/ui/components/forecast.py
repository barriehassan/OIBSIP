import customtkinter as ctk
from zoneinfo import ZoneInfo
from app.ui import theme as t
from app.ui.presentation import temperature


class ForecastCard(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        icons,
        date,
        data,
        *,
        selected,
        current,
        unit,
        command,
        width,
        observed_time=None,
    ):
        super().__init__(
            parent,
            width=width,
            height=198,
            corner_radius=25,
            fg_color=t.SELECTED if selected else t.PANEL,
        )
        self.pack_propagate(False)
        ink = t.INK if selected else t.TEXT
        secondary = "#35404a" if selected else t.MUTED
        title = date.strftime("%A" if selected else "%a")
        header = ctk.CTkFrame(
            self,
            fg_color="#a8ccdc" if selected else t.PANEL,
            bg_color=t.BG,
            background_corner_colors=(
                t.BG,
                t.BG,
                t.SELECTED if selected else t.PANEL,
                t.SELECTED if selected else t.PANEL,
            ),
            corner_radius=22,
            height=48,
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        self.select = t.button(
            header,
            title,
            command,
            width=88 if selected else width - 24,
            corner_radius=8,
            fg_color="#a8ccdc" if selected else t.PANEL,
            hover_color="#a9cbe4" if selected else "#34343b",
            text_color=ink,
            height=32,
        )
        self.select.pack(side="left", padx=(10, 0), pady=8)
        if selected:
            t.label(
                header, observed_time or date.strftime("%d %b"), size=12, color=ink
            ).pack(side="right", padx=(0, 12))
        icon = current.icon_id if current else data.icon_id if data else "unknown"
        if selected:
            middle = ctk.CTkFrame(self, fg_color="transparent")
            middle.pack(fill="x", padx=12, pady=(5, 0))
            value = (
                current.temperature_c
                if current
                else data.temperature_max_c if data else None
            )
            self.temperature_label = t.label(
                middle, temperature(value, unit), size=30, bold=True, color=ink
            )
            self.temperature_label.pack(side="left")
            ctk.CTkLabel(middle, text="", image=icons.image(icon, 62)).pack(
                side="right"
            )
            if current:
                detail = (
                    f"Humidity  {current.humidity_percent:g}%\n"
                    f"Wind  {current.wind_speed_kmh:g} km/h\n"
                    f"Feels like  {temperature(current.feels_like_c, unit)}"
                )
                basis = "Current estimate"
            else:
                detail = (
                    (
                        data.description
                        + "\nLow  "
                        + temperature(data.temperature_min_c, unit)
                    )
                    if data
                    else "No daily data"
                )
                basis = "Forecast high"
            t.label(
                self,
                detail,
                size=11,
                color=ink,
                justify="left",
                anchor="w",
                wraplength=width - 24,
            ).pack(fill="x", padx=14)
            t.label(self, basis, size=10, color=secondary, height=14).pack(
                anchor="w", padx=14, pady=(1, 0)
            )
        else:
            ctk.CTkLabel(self, text="", image=icons.image(icon, 60)).pack(pady=(12, 10))
            t.label(
                self,
                temperature(data.temperature_max_c, unit) if data else "—",
                size=22,
                color=ink,
                bold=True,
            ).pack()
            t.label(
                self, "High · " + date.strftime("%d %b"), size=10, color=secondary
            ).pack(pady=(2, 0))
        self.bind("<Button-1>", lambda e: command())

        def clickable(widget):
            for child in widget.winfo_children():
                if child is not self.select:
                    child.bind("<Button-1>", lambda e: command())
                    if isinstance(child, ctk.CTkFrame):
                        clickable(child)

        clickable(self)


class HourlyStrip(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.slots = ctk.CTkScrollableFrame(
            self,
            orientation="horizontal",
            height=72,
            fg_color="transparent",
            scrollbar_button_color="#35353b",
            corner_radius=0,
        )
        self.slots.pack(fill="x")

    def render(self, window, bundle, unit, icons):
        for child in self.slots.winfo_children():
            child.destroy()
        if not window.entries:
            t.label(self.slots, "Hourly forecast unavailable.", color=t.MUTED).pack(
                padx=12, pady=20
            )
            return
        for i, row in enumerate(window.entries):
            cell = ctk.CTkFrame(
                self.slots, fg_color=t.PANEL, corner_radius=14, width=142, height=70
            )
            cell.grid(row=0, column=i, padx=(0, 8))
            cell.grid_propagate(False)
            local = row.forecast_at.astimezone(ZoneInfo(bundle.timezone))
            t.label(cell, local.strftime("%d %b · %H:%M"), size=12, color=t.MUTED).grid(
                row=0, column=0, columnspan=2, padx=9, pady=(4, 0)
            )
            ctk.CTkLabel(cell, text="", image=icons.image(row.icon_id, 30)).grid(
                row=1, column=0, padx=(5, 0)
            )
            probability = (
                "—"
                if row.precipitation_probability is None
                else f"{row.precipitation_probability:g}%"
            )
            t.label(
                cell, temperature(row.temperature_c, unit) + "  " + probability, size=13
            ).grid(row=1, column=1, padx=(0, 8))


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, title, value, detail="Current conditions"):
        super().__init__(parent, fg_color=t.PANEL, corner_radius=16, height=67)
        t.label(self, title, size=12, color=t.MUTED).pack(
            anchor="w", padx=14, pady=(8, 0)
        )
        t.label(self, value, size=18, bold=True, wraplength=210).pack(
            anchor="w", padx=14, pady=(0, 8)
        )

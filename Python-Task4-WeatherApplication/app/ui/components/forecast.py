import customtkinter as ctk
from zoneinfo import ZoneInfo
from app.ui import theme as t
from app.ui.presentation import temperature


class ForecastCard(ctk.CTkFrame):
    def __init__(
        self, parent, icons, date, data, *, selected, current, unit, command, width
    ):
        super().__init__(
            parent,
            width=width,
            height=207,
            corner_radius=25,
            fg_color=t.SELECTED if selected else t.PANEL,
        )
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)
        ink = t.INK if selected else t.TEXT
        secondary = "#35404a" if selected else t.MUTED
        title = date.strftime("%A" if selected else "%a")
        self.select = t.button(
            self,
            title,
            command,
            width=width - 18,
            fg_color=t.SELECTED if selected else t.PANEL,
            hover_color="#a9cbe4" if selected else "#34343b",
            text_color=ink,
        )
        self.select.grid(row=0, column=0, padx=8, pady=(8, 0))
        self.select.bind("<Return>", lambda e: command())
        self.select.bind("<space>", lambda e: command())
        t.label(
            self,
            date.strftime("%d %b") + (" · high" if not selected else ""),
            size=12,
            color=secondary,
            height=18,
        ).grid(row=1, column=0)
        icon = current.icon_id if current else data.icon_id if data else "unknown"
        if selected:
            middle = ctk.CTkFrame(self, fg_color="transparent")
            middle.grid(row=2, column=0, sticky="ew", padx=12)
            value = (
                current.temperature_c
                if current
                else data.temperature_max_c if data else None
            )
            self.temperature_label = t.label(
                middle, temperature(value, unit), size=32, bold=True, color=ink
            )
            self.temperature_label.pack(side="left")
            ctk.CTkLabel(middle, text="", image=icons.image(icon, 60)).pack(
                side="right"
            )
            basis = "Now · current estimate" if current else "Forecast high"
            t.label(self, basis, size=12, color=secondary, height=18).grid(
                row=3, column=0
            )
            description = (
                current.description
                if current
                else data.description if data else "Unavailable"
            )
            t.label(
                self, description, size=13, color=ink, wraplength=width - 20, height=20
            ).grid(row=4, column=0, padx=8)
            detail = (
                f"Humidity {current.humidity_percent:g}%  ·  Wind {current.wind_speed_kmh:g} km/h"
                if current
                else (
                    "Low " + temperature(data.temperature_min_c, unit)
                    if data
                    else "No daily data"
                )
            )
            t.label(
                self, detail, size=12, color=secondary, wraplength=width - 20, height=28
            ).grid(row=5, column=0, padx=6, pady=(3, 0))
        else:
            ctk.CTkLabel(self, text="", image=icons.image(icon, 68)).grid(
                row=2, column=0, pady=(5, 1)
            )
            t.label(
                self,
                temperature(data.temperature_max_c, unit) if data else "—",
                size=23,
                color=ink,
                bold=True,
            ).grid(row=3, column=0)
            t.label(
                self,
                (
                    "Low " + temperature(data.temperature_min_c, unit)
                    if data
                    else "Unavailable"
                ),
                size=12,
                color=secondary,
            ).grid(row=4, column=0, pady=(2, 0))
        for child in self.winfo_children():
            if child is not self.select:
                child.bind("<Button-1>", lambda e: command())
        self.bind("<Button-1>", lambda e: command())


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

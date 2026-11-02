"""CustomTkinter dashboard. All widget access occurs on the Tk event loop."""

import tkinter as tk
from datetime import timedelta
from zoneinfo import ZoneInfo
import webbrowser
import customtkinter as ctk
from app.ui import theme as t
from .controller import Controller
from .presentation import (
    temperature,
    location_label,
    local_today,
    day_slots,
    hour_window,
    local_hour,
)
from .components.forecast import ForecastCard, HourlyStrip, StatCard
from .components.rain_chart import RainChart
from .components.global_map import GlobalMap
from .components.weather_icon import IconImages, fetch_icons, VALID_IDS
from .components.chrome import symbol


class SkyCastWindow(ctk.CTk):
    def __init__(self, controller=None, *, remote_icons=True):
        ctk.set_appearance_mode("dark")
        super().__init__()
        self.title("NOMOLI FORGE — SkyCast")
        self.configure(fg_color=t.OUTER)
        self.geometry(
            f"{min(1440,self.winfo_screenwidth()-40)}x{min(900,self.winfo_screenheight()-70)}"
        )
        self.minsize(
            min(1024, self.winfo_screenwidth() - 40),
            min(700, self.winfo_screenheight() - 70),
        )
        self.controller = controller or Controller()
        self.icons = IconImages()
        self.remote_icons = remote_icons
        self.dialog = None
        self.candidate_key = None
        self.poll_id = None
        self.minute_id = None
        self.resize_id = None
        self.last_width = 0
        self.closed = False
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.details_visible = False
        self.light_mode = False
        self.shell = ctk.CTkFrame(self, fg_color=t.BG, corner_radius=42)
        self.shell.pack(fill="both", expand=True, padx=60, pady=60)
        self.header = ctk.CTkFrame(self.shell, fg_color="transparent")
        self.header.pack(fill="x", padx=32, pady=(20, 20))
        self.header.columnconfigure(0, minsize=380)
        self.header.columnconfigure(1, weight=1)
        self.header.columnconfigure(2, minsize=290)
        self.identity = ctk.CTkFrame(self.header, fg_color="transparent")
        self.identity.grid(row=0, column=0, sticky="w", padx=(0, 24))
        self.menu_button = self.icon_button(self.identity, "grid", self.toggle_details)
        self.menu_button.pack(side="left", padx=(0, 14))
        self.notifications_button = self.icon_button(
            self.identity, "bell", self.notifications
        )
        self.notifications_button.pack(side="left", padx=(0, 22))
        self.pin_icon = ctk.CTkLabel(
            self.identity, text="", image=symbol("pin", t.TEXT, 22), width=22
        )
        self.pin_icon.pack(side="left", padx=(0, 10))
        self.location = t.label(
            self.identity, "Choose a city", size=13, anchor="w", width=174
        )
        self.location.pack(side="left")
        self.search_group = ctk.CTkFrame(
            self.header, fg_color=t.PANEL, corner_radius=24, width=480, height=40
        )
        self.search_group.grid(row=0, column=1, sticky="w")
        self.search_group.pack_propagate(False)
        self.search_button = t.button(
            self.search_group,
            "",
            self.search,
            width=36,
            image=symbol("search", t.MUTED, 20),
        )
        self.search_button.pack(side="left", padx=(10, 0))
        self.entry = ctk.CTkEntry(
            self.search_group,
            placeholder_text="Search city…",
            border_width=0,
            fg_color="transparent",
            height=40,
            font=t.font(14),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.entry.bind("<Return>", lambda e: self.search())
        self.entry.bind("<KeyRelease>", self.edited)
        self.utilities = ctk.CTkFrame(self.header, fg_color="transparent", width=220)
        self.utilities.grid(row=0, column=2, sticky="e", padx=(28, 0))
        self.sun_button = self.icon_button(
            self.utilities, "sun", lambda: self.set_theme(True)
        )
        self.sun_button.pack(side="left", padx=(0, 8))
        self.moon_button = self.icon_button(
            self.utilities, "moon", lambda: self.set_theme(False), selected=True
        )
        self.moon_button.pack(side="left", padx=(0, 22))
        self.profile_button = t.button(
            self.utilities,
            "S",
            self.about,
            width=42,
            height=42,
            fg_color="#37312a",
            text_color="#f0d9b1",
        )
        self.profile_button.pack(side="left")
        # Errors remain visible; routine retrieval details are in the bell panel.
        self.status_row = ctk.CTkFrame(self.shell, fg_color="transparent")
        self.status = t.label(self.status_row, "", size=12, color=t.MUTED, anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.retry_button = t.button(self.status_row, "Retry", self.retry, width=62)
        self.retry_button.pack(side="right", padx=(6, 0))
        self.cancel_button = t.button(self.status_row, "Cancel", self.cancel, width=62)
        self.cancel_button.pack(side="right")
        self.page = ctk.CTkScrollableFrame(
            self.shell,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=t.BG,
            scrollbar_button_hover_color=t.PANEL,
        )
        self.page.pack(fill="both", expand=True, padx=26, pady=(0, 22))
        self.page.columnconfigure(0, weight=1)
        self.page.columnconfigure(1, weight=0, minsize=280)
        tabs = ctk.CTkFrame(self.page, fg_color="transparent")
        tabs.grid(row=0, column=0, sticky="ew", pady=(0, 28))
        self.tab_buttons = {}
        for name in ("Today", "Tomorrow", "Next 7 Days"):
            button = t.button(
                tabs,
                name,
                lambda n=name: self.tab_changed(n),
                width=95 if name != "Next 7 Days" else 132,
                fg_color=t.BG,
            )
            button.pack(side="left", padx=(0, 4))
            self.tab_buttons[name] = button
        self.forecast_mode = ctk.CTkFrame(tabs, fg_color=t.PANEL, corner_radius=18)
        self.forecast_mode.pack(side="right")
        self.forecast_button = t.button(
            self.forecast_mode,
            "Forecast",
            self.toggle_details,
            width=102,
            fg_color=t.SELECTED,
            text_color=t.INK,
            height=30,
        )
        self.forecast_button.pack(side="left")
        self.air_button = t.button(
            self.forecast_mode, "Air quality", self.air_quality, width=94, height=30
        )
        self.air_button.pack(side="left")
        t.label(self.page, "Chance of rain", size=18).grid(
            row=0, column=1, sticky="w", padx=(30, 0), pady=(0, 28)
        )
        self.card_strip = ctk.CTkScrollableFrame(
            self.page,
            orientation="horizontal",
            height=201,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=t.PANEL,
        )
        self.card_strip.grid(row=1, column=0, sticky="ew")
        self.rain = RainChart(self.page)
        self.rain.grid(row=1, column=1, sticky="nsew", padx=(30, 0))
        map_head = ctk.CTkFrame(self.page, fg_color="transparent")
        map_head.grid(row=2, column=0, sticky="ew", pady=(18, 18))
        t.label(map_head, "Global map", size=20).pack(side="left")
        t.button(map_head, "View wide", self.wide_map, width=112, height=30).pack(
            side="right"
        )
        city_head = ctk.CTkFrame(self.page, fg_color="transparent")
        city_head.grid(row=2, column=1, sticky="ew", padx=(30, 0), pady=(18, 18))
        t.label(city_head, "Other large cities", size=18).pack(side="left")
        self.map_frame = ctk.CTkFrame(self.page, fg_color=t.MAP, corner_radius=26)
        self.map_frame.grid(row=3, column=0, sticky="nsew")
        self.map = GlobalMap(self.map_frame, self.choose, explore=self.map_help)
        self.map.pack(fill="both", expand=True, padx=8, pady=8)
        self.cities = ctk.CTkFrame(self.page, fg_color="transparent")
        self.cities.grid(row=3, column=1, sticky="nsew", padx=(30, 0))
        # Secondary controls do not displace the two-row reference composition.
        self.detail_panel = ctk.CTkFrame(self.page, fg_color="transparent")
        self.detail_panel.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        toolbar = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 10))
        t.label(toolbar, "Forecast details", size=18).pack(side="left")
        self.unit = ctk.CTkSegmentedButton(
            toolbar,
            values=["°C", "°F"],
            command=self.unit_changed,
            selected_color=t.SELECTED,
            text_color=t.INK,
            unselected_color="#a6a6af",
            width=90,
        )
        self.unit.set("°C")
        self.unit.pack(side="right", padx=10)
        self.refresh_button = t.button(toolbar, "Refresh", self.refresh, width=80)
        self.refresh_button.pack(side="right")
        self.add_button = t.button(
            toolbar, "+ Add current city", self.add_city, width=142
        )
        self.add_button.pack(side="right", padx=10)
        t.button(toolbar, "Full report", self.details, width=95).pack(side="right")
        hourly_head = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        hourly_head.pack(fill="x")
        self.hour_label = t.label(hourly_head, "Next six hours", size=12, color=t.MUTED)
        self.hour_label.pack(side="left")
        self.next_button = t.button(
            hourly_head, "Next", lambda: self.move_hours(1), width=50
        )
        self.next_button.pack(side="right")
        self.prev_button = t.button(
            hourly_head, "Previous", lambda: self.move_hours(-1), width=66
        )
        self.prev_button.pack(side="right", padx=5)
        self.hourly = HourlyStrip(self.detail_panel)
        self.hourly.pack(fill="x")
        self.rain_note = t.label(
            self.detail_panel,
            "Probability, not rainfall amount",
            size=12,
            color=t.MUTED,
        )
        self.rain_note.pack(anchor="w")
        self.stats_caption = t.label(
            self.detail_panel, "Current conditions", size=12, color=t.MUTED
        )
        self.stats_caption.pack(anchor="w", pady=(12, 6))
        self.stats = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        self.stats.pack(fill="x")
        footer = ctk.CTkFrame(self.detail_panel, fg_color="transparent")
        footer.pack(fill="x", pady=(12, 0))
        t.button(
            footer,
            "Weather: Open-Meteo",
            lambda: webbrowser.open("https://open-meteo.com/"),
            width=155,
            fg_color=t.BG,
        ).pack(side="left")
        t.label(
            footer,
            "GeoNames · Natural Earth · OpenWeather icons",
            size=12,
            color=t.MUTED,
        ).pack(side="left", padx=10)
        t.button(footer, "About & sources", self.about, width=120, fg_color=t.BG).pack(
            side="right"
        )
        self.detail_panel.grid_remove()
        self.bind("<Control-l>", lambda event: self.entry.focus_set())
        self.bind("<Control-u>", lambda event: self.toggle_unit())
        self.bind("<Configure>", self.resized)
        self.bind("<Escape>", lambda e: self.cancel())
        self.render()
        self.poll_id = self.after(80, self.poll)
        self.minute_id = self.after(60000, self.minute)

    def icon_button(self, parent, name, command, selected=False):
        return t.button(
            parent,
            "",
            command,
            width=42,
            height=42,
            corner_radius=21,
            fg_color=t.SELECTED if selected else t.PANEL,
            image=symbol(name, t.INK if selected else t.TEXT, 22),
        )

    def toggle_details(self):
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.detail_panel.grid()
            self.after_idle(lambda: self.page._parent_canvas.yview_moveto(1))
        else:
            self.detail_panel.grid_remove()
            self.page._parent_canvas.yview_moveto(0)

    def notifications(self):
        state = self.controller.state
        message = state.status or "No new activity. Search for a city to get started."
        if state.bundle:
            b = state.bundle
            message += (
                f"\n\n{location_label(b.location)}\nCurrent {temperature(b.current.temperature_c, state.unit)} · {b.current.description}"
                f"\nObserved: {local_hour(b.current.observed_at, b.timezone)}"
                f"\nDownloaded: {local_hour(b.retrieved_at, b.timezone)}"
            )
        self.text_dialog(
            "Activity · SkyCast",
            message
            + "\n\nThis panel shows search and retrieval activity, not weather alerts.",
        )

    def air_quality(self):
        self.text_dialog(
            "Air quality",
            "Air-quality data is not available from the connected weather provider.\n\nNo air-quality reading or health rating is shown. Use Forecast for available weather data.",
        )

    def map_help(self):
        self.text_dialog(
            "Explore the map",
            "Search a city to see its weather on the map.\n\nUse the grid menu or Forecast button to open details and add up to three cities.\n\nDrag to pan, use + / − to zoom, reset to return to the overview, layers to show or hide markers, and locate to center the active city.\n\nThe map shows land and your selected locations. Wind fields, ocean conditions and radar layers are not available.",
        )

    def set_theme(self, light):
        if light == self.light_mode:
            return
        self.light_mode = light
        dark = {
            "OUTER": "#292929",
            "BG": "#111015",
            "PANEL": "#1c1c1f",
            "TEXT": "#f5f5f7",
            "MUTED": "#aeacb8",
            "MAP": "#19191b",
        }
        bright = {
            "OUTER": "#dce3e8",
            "BG": "#f5f7fb",
            "PANEL": "#e4e9ef",
            "TEXT": "#17212c",
            "MUTED": "#526071",
            "MAP": "#19191b",
        }
        before, after = (dark, bright) if light else (bright, dark)
        mapping = {before[k]: after[k] for k in before if before[k] != after[k]}
        for key, value in after.items():
            setattr(t, key, value)

        def recolor(widget):
            # Only palette colors change; map artwork and blue-card ink stay fixed.
            if widget is self.map:
                return
            if isinstance(widget, ctk.CTkBaseClass) or widget is self:
                for option in (
                    "fg_color",
                    "bg_color",
                    "text_color",
                    "scrollbar_button_color",
                ):
                    try:
                        old = widget.cget(option)
                        if isinstance(old, str) and old in mapping:
                            widget.configure(**{option: mapping[old]})
                    except (ValueError, tk.TclError, AttributeError):
                        pass
            for child in widget.winfo_children():
                recolor(child)

        recolor(self)
        self.page.configure(fg_color=t.BG)
        self.card_strip.configure(fg_color=t.BG)
        self.hourly.slots.configure(fg_color=t.BG)
        self.entry.configure(placeholder_text_color=t.MUTED)
        self.search_button.configure(image=symbol("search", t.MUTED, 20))
        self.rain.configure(bg=t.BG)
        for button, name, selected in (
            (self.sun_button, "sun", light),
            (self.moon_button, "moon", not light),
        ):
            button.configure(
                fg_color=t.SELECTED if selected else t.PANEL,
                image=symbol(name, t.INK if selected else t.TEXT, 22),
            )
        self.menu_button.configure(image=symbol("grid", t.TEXT, 22))
        self.notifications_button.configure(image=symbol("bell", t.TEXT, 22))
        self.pin_icon.configure(image=symbol("pin", t.TEXT, 22))
        self.render()

    def edited(self, event):
        if event.keysym in (
            "Return",
            "Tab",
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
        ):
            return
        if self.controller.state.loading or self.controller.state.candidates:
            self.controller.invalidate()
            self.close_candidates()
            self.render_status()

    def search(self):
        self.close_candidates()
        self.controller.search(self.entry.get())
        self.render_status()

    def choose(self, location):
        self.close_candidates()
        self.controller.choose(location)
        self.render()

    def cancel(self):
        self.controller.invalidate()
        self.close_candidates()
        self.render_status()
        self.entry.focus_set()

    def refresh(self):
        self.controller.refresh()
        self.render_status()

    def retry(self):
        self.controller.retry()
        self.render_status()

    def toggle_unit(self):
        unit = "°F" if self.controller.state.unit == "°C" else "°C"
        self.unit.set(unit)
        self.unit_changed(unit)

    def unit_changed(self, unit):
        self.unit.set(unit)
        self.controller.set_unit(unit)
        self.render()

    def tab_changed(self, tab):
        self.controller.set_tab(tab)
        self.render()

    def select_day(self, day):
        self.controller.select_day(day)
        self.render()
        self.after_idle(self.focus_selected_card)

    def focus_selected_card(self):
        if self.closed or not self.controller.state.bundle:
            return
        state = self.controller.state
        index = (
            state.selected_date - local_today(state.bundle, self.controller.clock())
        ).days
        cards = self.card_strip.winfo_children()
        if 0 <= index < len(cards):
            cards[index].select.focus_set()

    def move_hours(self, step):
        self.controller.state.hour_page += step
        self.render()

    def add_city(self):
        self.controller.add_current_city()
        self.render()

    def remove_city(self, loc):
        self.controller.remove_city(loc)
        self.render()

    def refresh_city(self, loc):
        self.controller.refresh_city(loc)
        self.render()

    def poll(self):
        if self.closed:
            return
        changed = self.controller.drain()
        if self.controller.icon_version != getattr(self, "icon_version", 0):
            self.icons.accept(self.controller.icon_results)
            self.icon_version = self.controller.icon_version
            changed = True
        if changed:
            self.render()
        self.poll_id = self.after(80, self.poll)

    def minute(self):
        if self.closed:
            return
        self.controller.tick_dates()
        self.render()
        self.minute_id = self.after(60000, self.minute)

    def resized(self, event):
        if event.widget is not self:
            return
        width = self.winfo_width()
        if abs(width - self.last_width) < 10:
            return
        self.last_width = width
        if self.resize_id:
            self.after_cancel(self.resize_id)
        self.resize_id = self.after(140, self.reflow)

    def reflow(self):
        self.resize_id = None
        compact = self.winfo_width() < 1150
        self.shell.pack_configure(
            padx=24 if compact else 60, pady=20 if self.winfo_height() < 820 else 60
        )
        self.header.pack_configure(
            padx=24 if compact else 32,
            pady=(16, 8) if self.winfo_height() < 820 else (20, 20),
        )
        self.identity.grid_configure(padx=(0, 12 if compact else 24))
        self.location.configure(
            width=126 if compact else 174, wraplength=126 if compact else 174
        )
        self.utilities.grid_configure(padx=(12 if compact else 28, 0))
        self.header.columnconfigure(0, minsize=300 if compact else 380)
        self.header.columnconfigure(2, minsize=170 if compact else 240)
        self.search_group.configure(
            width=310 if compact else min(480, self.winfo_width() - 880)
        )
        self.page.columnconfigure(1, minsize=250 if compact else 280)
        self.forecast_mode.pack_forget()
        if not compact:
            self.forecast_mode.pack(side="right")
        self.map.configure(height=272 if self.winfo_height() < 820 else 306)
        self.status.configure(wraplength=max(500, self.winfo_width() - 350))
        self.update_idletasks()
        self.render()

    def render_status(self):
        s = self.controller.state
        previous = (
            " · Previous results retained"
            if s.bundle and (s.loading or s.failed)
            else ""
        )
        self.status.configure(
            text=s.status + previous, text_color=t.ERROR if s.failed else t.MUTED
        )
        if s.loading or s.failed or s.candidates:
            self.status_row.pack(
                fill="x", padx=32, pady=(0, 6), before=self.page._parent_frame
            )
        else:
            self.status_row.pack_forget()
        self.cancel_button.configure(
            state="normal" if s.loading or s.candidates else "disabled"
        )
        self.retry_button.configure(
            state="normal" if s.failed and self.controller.last_action else "disabled"
        )
        self.refresh_button.configure(
            state="normal" if s.bundle and not s.loading else "disabled"
        )

    def render(self):
        if self.closed:
            return
        s = self.controller.state
        b = s.bundle
        now = self.controller.clock()
        self.render_status()
        for name, button in self.tab_buttons.items():
            button.configure(
                text_color=t.TEXT if name == s.tab else t.MUTED,
                font=t.font(16, name == s.tab),
            )
        if s.candidates and self.candidate_key != s.candidates:
            self.show_candidates(s.candidates)
        for child in self.card_strip.winfo_children():
            child.destroy()
        for child in self.stats.winfo_children():
            child.destroy()
        if not b:
            self.location.configure(text="Choose a city")
            t.label(
                self.card_strip,
                "Your forecast starts here.\nSearch a city, country or supported postal code.",
                size=20,
                color=t.MUTED,
                justify="left",
            ).pack(padx=28, pady=65)
            self.rain.set_data(message="Rain forecast appears after a search")
            self.hour_label.configure(text="Next six hours · awaiting a location")
            self.prev_button.configure(state="disabled")
            self.next_button.configure(state="disabled")
            self.add_button.configure(state="disabled")
        else:
            self.add_button.configure(state="normal")
            tz = ZoneInfo(b.timezone)
            self.location.configure(text=f"{b.location.name}, {b.location.country}")
            slots = day_slots(b, now)
            today = local_today(b, now)
            if s.selected_date not in [d for d, _ in slots]:
                s.selected_date = today
            available = max(600, self.card_strip._parent_canvas.winfo_width() - 8)
            selected_width = 208
            small_width = max(78, int((available - selected_width - 60) / 6))
            if selected_width + 6 * small_width + 60 <= available:
                self.card_strip._scrollbar.grid_remove()
            else:
                self.card_strip._scrollbar.grid()
            for i, (date, data) in enumerate(slots):
                selected = date == s.selected_date
                card = ForecastCard(
                    self.card_strip,
                    self.icons,
                    date,
                    data,
                    selected=selected,
                    current=b.current if selected and date == today else None,
                    unit=s.unit,
                    command=lambda d=date: self.select_day(d),
                    width=selected_width if selected else small_width,
                    observed_time=(
                        b.current.observed_at.astimezone(tz)
                        .strftime("%I:%M %p")
                        .lstrip("0")
                        if selected and date == today
                        else None
                    ),
                )
                card.grid(row=0, column=i, padx=(0, 10))
                card.select.bind(
                    "<Left>",
                    lambda e, d=date: self.select_day(
                        max(today, d - timedelta(days=1))
                    ),
                )
                card.select.bind(
                    "<Right>",
                    lambda e, d=date: self.select_day(
                        min(today + timedelta(days=6), d + timedelta(days=1))
                    ),
                )
            # Scroll the expanded chronological slot into view after layout.
            self.after_idle(self.reveal_selected)
            window = hour_window(b, s.selected_date, now, s.hour_page)
            self.hour_label.configure(
                text=window.caption
                + (" · partial coverage / gaps" if window.incomplete else "")
            )
            self.prev_button.configure(
                state="normal" if window.previous else "disabled"
            )
            self.next_button.configure(
                state="normal" if window.following else "disabled"
            )
            self.hourly.render(window, b, s.unit, self.icons)
            self.rain.set_data(window.entries, b.timezone)
            self.rain_note.configure(
                text="Missing values shown as —\nProbability, not rainfall amount"
            )
            self.stats_caption.configure(
                text=f"Current conditions · {b.location.name} · downloaded {b.retrieved_at.astimezone(tz):%d %b %H:%M %Z}"
            )
            metrics = [
                ("Humidity", f"{b.current.humidity_percent:g}%"),
                ("Wind speed", f"{b.current.wind_speed_kmh:g} km/h"),
                ("Feels like", temperature(b.current.feels_like_c, s.unit)),
                ("Condition", b.current.description),
            ]
            for i, (name, value) in enumerate(metrics):
                self.stats.columnconfigure(i, weight=1, uniform="stats")
                StatCard(self.stats, name, value).grid(
                    row=0, column=i, sticky="ew", padx=(0, 10 if i < 3 else 0)
                )
            self.load_icons(b, slots, window)
        self.render_cities()
        self.map.set_markers(self.markers(), b.location if b else None)

    def reveal_selected(self):
        if self.closed or not self.controller.state.bundle:
            return
        # CTk horizontal scroll canvas; keep the selected card visible at narrow widths.
        children = self.card_strip.winfo_children()
        selected = (
            self.controller.state.selected_date
            - local_today(self.controller.state.bundle, self.controller.clock())
        ).days
        if 0 <= selected < len(children):
            card = children[selected]
            canvas = self.card_strip._parent_canvas
            total = max(1, self.card_strip.winfo_reqwidth())
            left = canvas.canvasx(0)
            right = left + canvas.winfo_width()
            if card.winfo_x() < left:
                canvas.xview_moveto(card.winfo_x() / total)
            elif card.winfo_x() + card.winfo_width() > right:
                canvas.xview_moveto(
                    (card.winfo_x() + card.winfo_width() - canvas.winfo_width()) / total
                )

    def render_cities(self):
        self.city_temperature_labels = []
        for child in self.cities.winfo_children():
            child.destroy()
        s = self.controller.state
        if not s.cities:
            for title, detail in [
                (
                    "Build your city list",
                    "Search a place, then use\n“Add current city” below.",
                ),
                ("Real weather, chosen by you", "Up to three cities this session."),
                ("Select a city to explore", "No automatic location tracking."),
            ]:
                frame = ctk.CTkFrame(self.cities, fg_color=t.PANEL, corner_radius=22)
                frame.pack(fill="x", pady=(0, 10))
                t.label(frame, title, size=14).pack(anchor="w", padx=16, pady=(14, 3))
                t.label(frame, detail, size=12, color=t.MUTED, justify="left").pack(
                    anchor="w", padx=16, pady=(0, 13)
                )
            return
        for loc, result in s.cities.items():
            frame = ctk.CTkFrame(
                self.cities,
                fg_color=t.PANEL,
                corner_radius=24,
                height=90 if self.winfo_height() < 820 else 98,
            )
            frame.pack(fill="x", pady=(0, 8))
            frame.pack_propagate(False)
            current = result.weather.current if result.weather else None
            left = ctk.CTkFrame(frame, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=(18, 4), pady=10)
            t.label(
                left, loc.country, size=10, color=t.MUTED, anchor="w", height=15
            ).pack(fill="x")
            name = t.button(
                left,
                loc.name,
                lambda l=loc: self.choose(l),
                width=90,
                height=27,
                anchor="w",
            )
            name.configure(font=t.font(16))
            name.pack(fill="x")
            detail = (
                "Updating…"
                if loc in s.city_loading
                else (
                    "Retry needed"
                    if result.error
                    else current.description if current else "Unavailable"
                )
            )
            t.label(
                left,
                detail,
                size=11,
                color=t.ERROR if result.error else t.MUTED,
                anchor="w",
                wraplength=145,
            ).pack(fill="x", pady=(4, 0))
            right = ctk.CTkFrame(frame, fg_color="transparent", width=64)
            right.pack(side="right", padx=(0, 14), pady=6)
            icon = ctk.CTkLabel(
                right,
                text="",
                image=self.icons.image(current.icon_id if current else "unknown", 43),
                height=43,
            )
            icon.pack()
            reading = t.label(
                right,
                temperature(current.temperature_c, s.unit) if current else "—",
                size=21,
                bold=True,
            )
            reading.pack()
            self.city_temperature_labels.append(reading)
            # Context actions leave the compact country / city / condition layout clear.
            for widget in (frame, name, icon, reading):
                widget.bind("<Button-3>", lambda e, l=loc: self.city_actions(l))
            name.bind("<Shift-F10>", lambda e, l=loc: self.city_actions(l))

    def city_actions(self, location):
        dialog = ctk.CTkToplevel(self)
        dialog.title(location.name)
        dialog.geometry("360x220")
        dialog.transient(self)
        t.label(dialog, location_label(location), wraplength=320).pack(pady=18)

        def action(callback):
            dialog.destroy()
            callback(location)

        for label, callback in (
            ("View weather", self.choose),
            ("Update weather", self.refresh_city),
            ("Remove city", self.remove_city),
        ):
            t.button(dialog, label, lambda c=callback: action(c), width=200).pack(
                pady=5
            )
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def markers(self):
        s = self.controller.state
        result = {loc: r.weather for loc, r in s.cities.items()}
        if s.bundle:
            result[s.bundle.location] = s.bundle
        return list(result.items())

    def load_icons(self, bundle, slots, window):
        if not self.remote_icons:
            return
        ids = (
            {bundle.current.icon_id}
            | {r.icon_id for _, r in slots if r}
            | {r.icon_id for r in window.entries}
        )
        ids |= {
            r.weather.current.icon_id
            for r in self.controller.state.cities.values()
            if r.weather
        }
        missing = (ids & VALID_IDS) - self.icons.attempted
        if missing:
            self.icons.attempted.update(missing)
            self.controller.request_icons(missing)

    def show_candidates(self, locations):
        self.close_candidates()
        self.candidate_key = locations
        dialog = ctk.CTkToplevel(self)
        self.dialog = dialog
        dialog.title("Choose a location")
        dialog.geometry("610x390")
        dialog.transient(self)
        t.label(dialog, "Choose the matching location", size=19, bold=True).pack(
            anchor="w", padx=20, pady=16
        )
        scroll = ctk.CTkScrollableFrame(dialog, fg_color=t.BG)
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        buttons = []
        for loc in locations:
            btn = t.button(
                scroll, location_label(loc), lambda l=loc: self.choose(l), width=550
            )
            btn.pack(fill="x", padx=6, pady=5)
            buttons.append(btn)
        for i, btn in enumerate(buttons):
            btn.bind(
                "<Down>", lambda e, j=i: buttons[(j + 1) % len(buttons)].focus_set()
            )
            btn.bind("<Up>", lambda e, j=i: buttons[(j - 1) % len(buttons)].focus_set())
            btn.bind("<Return>", lambda e, l=locations[i]: self.choose(l))
        dialog.bind("<Escape>", lambda e: self.cancel())
        dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        if buttons:
            dialog.after(50, buttons[0].focus_set)

    def close_candidates(self):
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.destroy()
        self.dialog = None
        self.candidate_key = None

    def text_dialog(self, title, text):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("690x490")
        dialog.transient(self)
        area = ctk.CTkTextbox(dialog, wrap="word", font=t.font(14))
        area.pack(fill="both", expand=True, padx=20, pady=20)
        area.insert("1.0", text)
        area.configure(state="disabled")
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        t.button(dialog, "Close", dialog.destroy, width=90).pack(pady=(0, 14))

    def details(self):
        s = self.controller.state
        b = s.bundle
        if not b:
            self.text_dialog(
                "Forecast details", "Search a location to view its forecast."
            )
            return
        window = hour_window(b, s.selected_date, self.controller.clock(), s.hour_page)
        lines = [
            location_label(b.location),
            f"Timezone: {b.timezone}",
            f"Provider valid time: {local_hour(b.current.observed_at,b.timezone)}",
            f"Downloaded: {local_hour(b.retrieved_at,b.timezone)}",
            "",
            window.caption,
        ]
        for r in window.entries:
            prob = (
                "Unavailable"
                if r.precipitation_probability is None
                else f"{r.precipitation_probability:g}%"
            )
            lines.append(
                f"{local_hour(r.forecast_at,b.timezone)} · {temperature(r.temperature_c,s.unit,1)} · {r.description} · Rain {prob}"
            )
        lines += ["", "Daily summaries (high / low):"]
        for d, r in day_slots(b, self.controller.clock()):
            lines.append(
                f"{d}: "
                + (
                    f"{temperature(r.temperature_max_c,s.unit,1)} / {temperature(r.temperature_min_c,s.unit,1)} · {r.description}\n  Basis: {r.source}"
                    if r
                    else "Unavailable"
                )
            )
        if window.incomplete:
            lines.append("\nPartial hourly coverage. Gaps are not interpolated.")
        self.text_dialog("Forecast details", "\n".join(lines))

    def wide_map(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Global map · selected locations")
        dialog.geometry("1040x600")
        dialog.transient(self)
        view = GlobalMap(dialog, self.choose, explore=self.map_help)
        view.pack(fill="both", expand=True, padx=20, pady=20)
        b = self.controller.state.bundle
        view.set_markers(self.markers(), b.location if b else None)
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        t.button(dialog, "Close", dialog.destroy, width=90).pack(pady=(0, 12))

    def about(self):
        self.text_dialog(
            "About SkyCast",
            "NOMOLI FORGE — SkyCast\nKnow the Sky. Plan Your Day.\n\nWeather: Open-Meteo · CC BY 4.0\nhttps://open-meteo.com/\nGeocoding: Open-Meteo / GeoNames\nMap: Natural Earth, public domain; equirectangular land silhouette.\nhttps://www.naturalearthdata.com/\n\nIcons: official OpenWeather hosted assets, fetched into memory when available. Original SkyCast illustrations are the offline fallback.\nhttps://openweathermap.org/weather-conditions\n\nCurrent conditions are model estimates. Local-day corrections and temperature conversions are performed by SkyCast. Map pins represent selected places only, not global live coverage.\n\nCity choices last only for this session. Favorites, persistent weather caching, speech, IP detection and the temperature trend chart are not implemented.\n\nEducational noncommercial API usage. Windows verification remains pending.",
        )

    def close(self):
        if self.closed:
            return
        self.closed = True
        for ident in (self.poll_id, self.minute_id, self.resize_id):
            if ident:
                try:
                    self.after_cancel(ident)
                except tk.TclError:
                    pass
        self.controller.close()
        if self.light_mode:
            self.set_theme(False)
        self.destroy()

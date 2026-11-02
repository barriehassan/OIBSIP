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
        self.shell = ctk.CTkFrame(self, fg_color=t.BG, corner_radius=32)
        self.shell.pack(fill="both", expand=True, padx=22, pady=20)
        self.header = ctk.CTkFrame(self.shell, fg_color="transparent")
        self.header.pack(fill="x", padx=26, pady=(18, 4))
        self.header.columnconfigure(1, weight=1)
        identity = ctk.CTkFrame(self.header, fg_color="transparent")
        identity.grid(row=0, column=0, sticky="w", padx=(0, 20))
        t.button(identity, "S", self.about, width=38, fg_color=t.PANEL).pack(
            side="left", padx=(0, 9)
        )
        brand = ctk.CTkFrame(identity, fg_color="transparent")
        brand.pack(side="left")
        t.label(brand, "SkyCast", size=18, bold=True).pack(anchor="w")
        t.label(brand, "NOMOLI FORGE", size=10, color=t.MUTED).pack(anchor="w")
        self.search_group = ctk.CTkFrame(
            self.header, fg_color="#202023", corner_radius=24
        )
        self.search_group.grid(row=0, column=1, sticky="ew", padx=(0, 18))
        self.entry = ctk.CTkEntry(
            self.search_group,
            placeholder_text="Search city, country or postal code…",
            border_width=0,
            fg_color="transparent",
            height=40,
            font=t.font(14),
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(14, 0), pady=3)
        self.search_button = t.button(
            self.search_group, "Search", self.search, width=76
        )
        self.search_button.pack(side="right", padx=5)
        self.entry.bind("<Return>", lambda e: self.search())
        self.entry.bind("<KeyRelease>", self.edited)
        self.utilities = ctk.CTkFrame(self.header, fg_color="transparent")
        self.utilities.grid(row=0, column=2, sticky="e")
        self.unit = ctk.CTkSegmentedButton(
            self.utilities,
            values=["°C", "°F"],
            command=self.unit_changed,
            selected_color=t.SELECTED,
            selected_hover_color="#a7cbe6",
            unselected_color="#a6a6af",
            unselected_hover_color="#b6b6bf",
            text_color=t.INK,
            text_color_disabled=t.MUTED,
            font=t.font(14),
            width=110,
            height=36,
        )
        self.unit.set("°C")
        self.unit.pack(side="left", padx=(0, 10))
        self.refresh_button = t.button(
            self.utilities, "Refresh", self.refresh, width=76
        )
        self.refresh_button.pack(side="left")
        self.location = t.label(
            self.shell,
            "Know the Sky. Plan Your Day.",
            size=13,
            color=t.MUTED,
            anchor="w",
            wraplength=1200,
            justify="left",
        )
        self.location.pack(fill="x", padx=29, pady=(0, 2))
        status_row = ctk.CTkFrame(self.shell, fg_color="transparent")
        status_row.pack(fill="x", padx=28)
        self.status = t.label(status_row, "", size=12, color=t.MUTED, anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.retry_button = t.button(status_row, "Retry", self.retry, width=62)
        self.retry_button.pack(side="right", padx=(6, 0))
        self.cancel_button = t.button(status_row, "Cancel", self.cancel, width=62)
        self.cancel_button.pack(side="right")
        self.page = ctk.CTkScrollableFrame(
            self.shell,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#38383f",
        )
        self.page.pack(fill="both", expand=True, padx=18, pady=(2, 12))
        self.page.columnconfigure(0, weight=1)
        self.page.columnconfigure(1, weight=0, minsize=300)
        tabs = ctk.CTkFrame(self.page, fg_color="transparent")
        tabs.grid(row=0, column=0, sticky="ew", pady=(3, 6))
        self.tab_buttons = {}
        for name in ("Today", "Tomorrow", "Next 7 Days"):
            b = t.button(
                tabs, name, lambda n=name: self.tab_changed(n), width=110, fg_color=t.BG
            )
            b.pack(side="left", padx=(0, 8))
            self.tab_buttons[name] = b
        t.label(self.page, "Chance of rain", size=18).grid(
            row=0, column=1, sticky="w", padx=(26, 0), pady=(3, 6)
        )
        self.card_strip = ctk.CTkScrollableFrame(
            self.page,
            orientation="horizontal",
            height=218,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#35353b",
        )
        self.card_strip.grid(row=1, column=0, sticky="ew")
        self.rain = RainChart(self.page)
        self.rain.grid(row=1, column=1, sticky="nsew", padx=(24, 4), pady=(0, 12))
        hourly_head = ctk.CTkFrame(self.page, fg_color="transparent")
        hourly_head.grid(row=2, column=0, sticky="ew", pady=(3, 0))
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
        t.button(self.page, "Forecast details", self.details, width=120).grid(
            row=2, column=1, sticky="e", padx=4
        )
        self.hourly = HourlyStrip(self.page)
        self.hourly.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        self.rain_note = t.label(
            self.page,
            "Probability, not rainfall amount",
            size=12,
            color=t.MUTED,
            wraplength=235,
        )
        self.rain_note.grid(row=3, column=1, padx=(24, 0), sticky="n", pady=12)
        map_head = ctk.CTkFrame(self.page, fg_color="transparent")
        map_head.grid(row=4, column=0, sticky="ew", pady=(7, 10))
        t.label(map_head, "Global map", size=20).pack(side="left")
        t.button(map_head, "View wide", self.wide_map, width=105).pack(side="right")
        t.label(self.page, "Other large cities", size=18).grid(
            row=4, column=1, sticky="w", padx=(26, 0), pady=(7, 10)
        )
        self.map_frame = ctk.CTkFrame(self.page, fg_color=t.MAP, corner_radius=24)
        self.map_frame.grid(row=5, column=0, sticky="nsew")
        self.map = GlobalMap(self.map_frame, self.choose)
        self.map.pack(fill="both", expand=True, padx=12, pady=12)
        self.cities = ctk.CTkFrame(self.page, fg_color="transparent")
        self.cities.grid(row=5, column=1, sticky="nsew", padx=(24, 0))
        stat_head = ctk.CTkFrame(self.page, fg_color="transparent")
        stat_head.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 5))
        self.stats_caption = t.label(
            stat_head, "Current conditions", size=12, color=t.MUTED
        )
        self.stats_caption.pack(side="left")
        self.add_button = t.button(
            stat_head, "+ Add current city", self.add_city, width=135
        )
        self.add_button.pack(side="right")
        self.stats = ctk.CTkFrame(self.page, fg_color="transparent")
        self.stats.grid(row=7, column=0, columnspan=2, sticky="ew")
        footer = ctk.CTkFrame(self.page, fg_color="transparent")
        footer.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
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
        self.bind("<Control-l>", lambda event: self.entry.focus_set())
        self.bind("<Control-u>", lambda event: self.toggle_unit())
        self.bind("<Configure>", self.resized)
        self.bind("<Escape>", lambda e: self.cancel())
        self.render()
        self.poll_id = self.after(80, self.poll)
        self.minute_id = self.after(60000, self.minute)

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
        self.search_group.grid_forget()
        self.search_group.grid(
            row=1 if compact else 0,
            column=0 if compact else 1,
            columnspan=3 if compact else 1,
            sticky="ew",
            padx=0 if compact else (0, 18),
            pady=(8, 0) if compact else 0,
        )
        self.page.columnconfigure(1, minsize=232 if compact else 300)
        self.location.configure(wraplength=max(650, self.winfo_width() - 120))
        self.status.configure(wraplength=max(550, self.winfo_width() - 300))
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
            self.location.configure(text="Know the Sky. Plan Your Day.")
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
            self.location.configure(
                text=f"{location_label(b.location)}  ·  Current {temperature(b.current.temperature_c,s.unit)}  {b.current.description}  ·  As of {b.current.observed_at.astimezone(tz):%H:%M %Z}"
            )
            slots = day_slots(b, now)
            today = local_today(b, now)
            if s.selected_date not in [d for d, _ in slots]:
                s.selected_date = today
            available = max(880, self.card_strip._parent_canvas.winfo_width() - 12)
            selected_width = 230
            small_width = max(94, int((available - selected_width - 60) / 6))
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
            frame = ctk.CTkFrame(self.cities, fg_color=t.PANEL, corner_radius=22)
            frame.pack(fill="x", pady=(0, 8))
            current = result.weather.current if result.weather else None
            top = ctk.CTkFrame(frame, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(6, 0))
            name = t.button(top, loc.name, lambda l=loc: self.choose(l), width=125)
            name.pack(side="left")
            t.button(top, "×", lambda l=loc: self.remove_city(l), width=24).pack(
                side="right"
            )
            body = ctk.CTkFrame(frame, fg_color="transparent")
            body.pack(fill="x", padx=16)
            body.columnconfigure(0, weight=1)
            t.label(
                body, loc.country, size=12, color=t.MUTED, wraplength=80, justify="left"
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                body,
                text="",
                image=self.icons.image(current.icon_id if current else "unknown", 30),
            ).grid(row=0, column=1, padx=4)
            reading = t.label(
                body,
                temperature(current.temperature_c, s.unit) if current else "—",
                size=22,
                bold=True,
            )
            reading.grid(row=0, column=2, sticky="e")
            self.city_temperature_labels.append(reading)
            detail = (
                "Updating…"
                if loc in s.city_loading
                else (
                    "Previous data · retry"
                    if result.error and current
                    else (
                        "Unavailable · retry"
                        if result.error
                        else current.description if current else "Unavailable"
                    )
                )
            )
            bottom = ctk.CTkFrame(frame, fg_color="transparent")
            bottom.pack(fill="x", padx=12, pady=(0, 4))
            t.label(
                bottom, detail, size=12, color=t.ERROR if result.error else t.MUTED
            ).pack(side="left")
            t.button(
                bottom,
                "Retry" if result.error else "Update",
                lambda l=loc: self.refresh_city(l),
                width=54,
            ).pack(side="right")

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
        view = GlobalMap(dialog, self.choose)
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
        self.destroy()

"""Compact Task 05 controls using the existing controller and detail area."""

import customtkinter as ctk
from app.ui import theme as t
from app.ui.presentation import hour_window, location_label, local_hour
from app.ui.enhancement_data import metrics, solar_text
from app.ui.components.temperature_chart import TemperatureChart
from app.ui.components.forecast import StatCard
from app.services.cache_service import provenance, cache_kind
from app.services.voice_service import VoiceService, speech_text
from app.services.ip_location_service import CONSENT
from app.storage.local import StorageError


class Enhancements:
    def __init__(self, window, store=None, voice=None, notice=""):
        self.window = window
        self.store = store
        self.voice = voice or VoiceService()
        self.notice = notice
        self.voice_key = None
        self.approximate_key = None
        self.controls = ctk.CTkFrame(window.header, fg_color="transparent")
        self.controls.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(5, 0))
        self.listen = t.button(
            self.controls,
            "♪ Listen to Weather",
            self.toggle_voice,
            width=150,
            height=26,
            fg_color=t.BG,
        )
        self.listen.pack(side="left")
        self.star = t.button(
            self.controls,
            "☆ Save",
            self.save_favorite,
            width=75,
            height=26,
            fg_color=t.BG,
        )
        self.star.pack(side="left", padx=3)
        self.favorites_button = t.button(
            self.controls,
            "Favorites",
            self.show_favorites,
            width=90,
            height=26,
            fg_color=t.BG,
        )
        self.favorites_button.pack(side="left")
        self.detect = t.button(
            self.controls,
            "Detect My Location",
            self.request_location,
            width=145,
            height=26,
            fg_color=t.BG,
        )
        self.detect.pack(side="left", padx=(8, 10))
        self.indicator = t.label(
            self.controls,
            "",
            size=10,
            color=t.MUTED,
            anchor="e",
            wraplength=560,
            height=26,
        )
        self.indicator.pack(side="right", fill="x", expand=True)
        self.panel = ctk.CTkFrame(window.detail_panel, fg_color="transparent")
        self.panel.pack(fill="x", pady=10)
        self.solar = t.label(
            self.panel, "Sunrise / sunset appear after a search", size=13, anchor="w"
        )
        self.solar.pack(fill="x", pady=(0, 3))
        t.label(
            self.panel,
            "Unavailable solar times may reflect missing data or unusual daylight conditions.",
            size=10,
            color=t.MUTED,
            anchor="w",
        ).pack(fill="x")
        t.label(
            self.panel,
            "Hourly temperature · selected six-hour window",
            size=16,
            anchor="w",
        ).pack(fill="x", pady=(12, 5))
        self.chart = TemperatureChart(self.panel)
        self.chart.pack(fill="x")
        self.local_actions = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.local_actions.pack(fill="x", pady=8)
        t.button(
            self.local_actions, "Clear weather cache", self.clear_cache, width=160
        ).pack(side="left")
        self.feedback = t.label(
            self.local_actions, notice, size=11, color=t.MUTED, wraplength=680
        )
        self.feedback.pack(side="left", padx=12)
        self.favorite_list = ctk.CTkFrame(
            self.panel, fg_color=t.PANEL, corner_radius=18
        )
        self.consent_panel = ctk.CTkFrame(
            self.panel, fg_color=t.PANEL, corner_radius=18
        )
        self.result_panel = ctk.CTkFrame(self.panel, fg_color=t.PANEL, corner_radius=18)

    def expand(self):
        if not self.window.details_visible:
            self.window.toggle_details()
        self.window.after(100, lambda: self.window.page._parent_canvas.yview_moveto(1))

    def storage_action(self, callback):
        if not self.store:
            self.feedback.configure(
                text=self.notice
                or "Local storage unavailable; weather search still works."
            )
            self.expand()
            return None
        try:
            return callback()
        except StorageError as exc:
            self.feedback.configure(text=str(exc))
            self.expand()
            return None

    def save_favorite(self):
        b = self.window.controller.state.bundle
        if not b:
            return

        def save():
            self.store.add_favorite(b.location)
            self.feedback.configure(text=f"Saved {location_label(b.location)} locally.")
            self.star.configure(text="★ Saved")

        self.storage_action(save)
        if self.favorite_list.winfo_manager():
            self.show_favorites()

    def show_favorites(self):
        self.expand()
        for child in self.favorite_list.winfo_children():
            child.destroy()
        self.favorite_list.pack(fill="x", pady=8)
        t.label(self.favorite_list, "Saved locations", size=16).pack(
            anchor="w", padx=12, pady=8
        )
        result = self.storage_action(self.store.favorites) if self.store else None
        if result is None:
            t.label(
                self.favorite_list, "Local favorites unavailable.", color=t.MUTED
            ).pack(pady=10)
            return
        locations, invalid = result
        if not locations:
            t.label(
                self.favorite_list,
                "No favorites yet. Search for a city, then select ☆ Save.",
                color=t.MUTED,
            ).pack(pady=10)
        for loc in locations:
            row = ctk.CTkFrame(self.favorite_list, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)
            t.button(
                row,
                location_label(loc),
                lambda l=loc: self.window.choose(l),
                width=440,
                anchor="w",
            ).pack(side="left", fill="x", expand=True)
            t.button(row, "Remove", lambda l=loc: self.remove(l), width=80).pack(
                side="right", padx=6
            )
        if invalid:
            t.label(
                self.favorite_list,
                f"{invalid} invalid saved entries were skipped. Weather search is still available.",
                color=t.ERROR,
            ).pack(pady=8)

    def remove(self, location):
        self.storage_action(lambda: self.store.remove_favorite(location))
        self.show_favorites()
        self.star.configure(text="☆ Save")

    def clear_cache(self):
        def clear():
            self.store.clear_cache()
            self.feedback.configure(
                text="Weather cache cleared. Favorites and the displayed snapshot are retained."
            )

        self.storage_action(clear)

    def request_location(self):
        self.expand()
        for child in self.consent_panel.winfo_children():
            child.destroy()
        self.consent_panel.pack(fill="x", pady=8)
        t.label(
            self.consent_panel,
            CONSENT,
            size=13,
            wraplength=max(600, self.window.winfo_width() - 250),
            justify="left",
        ).pack(fill="x", padx=14, pady=12)
        row = ctk.CTkFrame(self.consent_panel, fg_color="transparent")
        row.pack(pady=(0, 12))
        t.button(
            row, "Continue with IP lookup", self.confirm_detection, width=200
        ).pack(side="left", padx=5)
        t.button(row, "Cancel", self.consent_panel.pack_forget, width=90).pack(
            side="left", padx=5
        )

    def confirm_detection(self):
        # Reachable only through the explicitly displayed consent panel.
        if not self.consent_panel.winfo_manager():
            return
        self.consent_panel.pack_forget()
        self.result_panel.pack_forget()
        self.approximate_key = None
        self.voice.stop()
        self.window.controller.detect_location(consent=True)
        self.window.render_status()

    def approximate_result(self, location):
        self.expand()
        self.result_panel.pack(fill="x", pady=8)
        for child in self.result_panel.winfo_children():
            child.destroy()
        t.label(
            self.result_panel,
            f"Approximate result · IPWHOIS.IO\n{location_label(location)}\n{location.latitude:.3f}, {location.longitude:.3f} · VPNs/proxies may affect this result.",
            wraplength=750,
        ).pack(pady=10)
        row = ctk.CTkFrame(self.result_panel, fg_color="transparent")
        row.pack(pady=8)

        def use():
            self.result_panel.pack_forget()
            self.window.choose(location)

        def reject():
            self.result_panel.pack_forget()
            self.window.cancel()
            self.window.entry.focus_set()

        t.button(row, "Use this location", use, width=150).pack(side="left", padx=5)
        t.button(row, "Search manually", reject, width=150).pack(side="left", padx=5)

    def toggle_voice(self):
        if self.voice.active:
            self.voice.stop()
        else:
            state = self.window.controller.state
            self.voice.start(
                speech_text(
                    state.bundle,
                    state.unit,
                    state.cache_source != "network"
                    or (
                        state.bundle is not None
                        and cache_kind(state.bundle, self.window.controller.clock())
                        == "stale cache"
                    ),
                )
            )
            if self.voice.status == "Unavailable":
                self.feedback.configure(
                    text="Local Windows speech is unavailable. Install requirements and check the Windows voice/audio settings."
                )
                self.expand()
        self.voice_label()

    def voice_label(self):
        state = self.voice.status
        label = (
            "Speaking · Stop"
            if state == "Speaking"
            else (
                "Starting · Stop"
                if state == "Starting"
                else (
                    "Stopping…"
                    if state == "Stopping"
                    else (
                        "Voice unavailable"
                        if state == "Unavailable"
                        else (
                            "Voice error · Retry"
                            if state == "Error"
                            else "♪ Listen to Weather"
                        )
                    )
                )
            )
        )
        self.listen.configure(
            text=label,
            state="normal" if self.window.controller.state.bundle else "disabled",
        )

    def poll(self):
        if self.voice.poll():
            self.voice_label()

    def render(self):
        state = self.window.controller.state
        b = state.bundle
        key = (b.location, b.retrieved_at, state.unit) if b else None
        if key != self.voice_key:
            self.voice.stop()
            self.voice_key = key
            self.star.configure(text="☆ Save")
        self.voice_label()
        self.star.configure(state="normal" if b else "disabled")
        if state.approximate and state.approximate != self.approximate_key:
            self.approximate_key = state.approximate
            self.approximate_result(state.approximate)
        if not state.approximate:
            self.result_panel.pack_forget()
        if not b:
            self.indicator.configure(text=self.notice)
            return
        source = state.cache_source
        if source in ("recent cache", "stale cache"):
            source = cache_kind(b, self.window.controller.clock())
        self.indicator.configure(text=provenance(b, source, state.offline))
        if state.storage_notice:
            self.feedback.configure(text=state.storage_notice)
        window = hour_window(
            b, state.selected_date, self.window.controller.clock(), state.hour_page
        )
        self.chart.set_data(window.entries, state.unit, b.timezone)
        self.solar.configure(
            text=solar_text(b, state.selected_date, self.window.controller.clock())
        )
        for child in self.window.stats.winfo_children():
            child.destroy()
        for i, (name, value, detail) in enumerate(
            metrics(b, state.unit, self.window.controller.clock())
        ):
            StatCard(self.window.stats, name, value, detail).grid(
                row=0, column=i, sticky="ew", padx=(0, 10 if i < 3 else 0)
            )
        if source != "network":
            self.window.stats_caption.configure(
                text="Last retrieved conditions · "
                + local_hour(b.retrieved_at, b.timezone)
            )

    def close(self):
        self.voice.close()

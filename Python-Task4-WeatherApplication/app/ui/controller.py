"""Tk-free state machine and fixed-size worker pool with replaceable pending work."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from queue import Queue, Empty
from threading import Condition, Thread
from time import monotonic
import requests
from app.core.exceptions import (
    SkyCastError,
    WeatherProviderError,
    WeatherRateLimitError,
    LocationValidationError,
)
from app.core.validator import normalize_query
from app.providers.http import JsonClient
from app.providers.geocoding import OpenMeteoGeocoding
from app.providers.open_meteo import OpenMeteoWeather
from app.services.weather_service import WeatherService, LocationWeatherResult
from .presentation import local_today


class LatestWorkers:
    """Two workers, at most five pending scopes. Worker code never touches Tk.

    Superseded queued tasks are replaced, not accumulated. Active HTTP requests
    cannot be forcibly cancelled; close discards results and joins briefly.
    Daemon workers prevent a stuck third-party socket from holding process exit.
    """

    def __init__(self):
        self.condition = Condition()
        self.pending = {}
        self.results = Queue()
        self.closed = False
        self.threads = [
            Thread(target=self._run, daemon=True, name=f"SkyCast-{i}") for i in range(2)
        ]
        for thread in self.threads:
            thread.start()

    def submit(self, scope, token, action):
        with self.condition:
            if self.closed:
                return
            if scope not in self.pending and len(self.pending) >= 5:
                raise RuntimeError("Worker queue capacity exceeded")
            self.pending[scope] = (token, action)
            self.condition.notify()

    def cancel(self, scope):
        with self.condition:
            self.pending.pop(scope, None)

    def _run(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.closed or self.pending)
                if self.closed:
                    return
                scope = next(iter(self.pending))
                token, action = self.pending.pop(scope)
            try:
                value, error = action(), None
            except SkyCastError as exc:
                value, error = None, exc
            except Exception as exc:
                value, error = None, WeatherProviderError(
                    "This request could not be completed. Please retry."
                )
                error.__cause__ = exc
            with self.condition:
                if not self.closed:
                    self.results.put((scope, token, value, error))

    def close(self):
        with self.condition:
            self.closed = True
            self.pending.clear()
            self.condition.notify_all()
        for thread in self.threads:
            thread.join(timeout=0.1)
        while not self.results.empty():
            self.results.get_nowait()


class Backend:
    def search(self, query):
        with requests.Session() as session:
            return OpenMeteoGeocoding(JsonClient(session)).search_locations(query)

    def weather(self, location):
        with requests.Session() as session:
            return WeatherService(OpenMeteoWeather(JsonClient(session))).get_weather(
                location
            )


@dataclass
class DisplayState:
    bundle: object = None
    candidates: tuple = ()
    query: str = ""
    status: str = "Search a city to explore its weather."
    loading: bool = False
    failed: bool = False
    tab: str = "Today"
    selected_date: object = None
    unit: str = "°C"
    hour_page: int = 0
    cities: dict = field(default_factory=dict)
    city_loading: set = field(default_factory=set)


class Controller:
    def __init__(self, backend=None, workers=None, clock=None, tick=monotonic):
        self.backend = backend or Backend()
        self.workers = workers or LatestWorkers()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.tick = tick
        self.state = DisplayState()
        self.generation = 0
        self.city_generation = {}
        self.closed = False
        self.last_action = None
        self.retry_at = 0
        self.icon_results = {}
        self.icon_version = 0
        self.icon_pending = set()

    def invalidate(self):
        self.generation += 1
        self.workers.cancel("main")
        self.state.candidates = ()
        if self.state.loading:
            self.state.status = (
                "Search cancelled. Previous results remain."
                if self.state.bundle
                else "Search cancelled."
            )
        self.state.loading = False

    def _allowed(self):
        if self.closed:
            return False
        if self.tick() < self.retry_at:
            self.state.status = (
                f"Service busy. Retry in {int(self.retry_at-self.tick())+1}s."
            )
            self.state.failed = True
            return False
        return True

    def search(self, query):
        if self.closed:
            return
        if self.state.loading and self.last_action == ("search", query):
            return
        self.invalidate()
        try:
            query = normalize_query(query)
        except LocationValidationError as exc:
            self.last_action = None
            self.state.status, self.state.failed = str(exc), True
            return
        if not self._allowed():
            return
        self.state.query = query
        self.last_action = ("search", query)
        self.state.status, self.state.loading, self.state.failed = (
            "Searching locations…",
            True,
            False,
        )
        token = (self.generation, "search")
        self.workers.submit("main", token, lambda: self.backend.search(query))

    def choose(self, location, *, force=False):
        if self.closed:
            return
        if self.state.loading and self.last_action == ("weather", location):
            return
        self.invalidate()
        if not self._allowed():
            return
        self.last_action = ("weather", location)
        saved = self.state.cities.get(location)
        if saved and saved.weather and not saved.error and not force:
            self.state.bundle = saved.weather
            self.state.tab = "Today"
            self.state.selected_date = local_today(saved.weather, self.clock())
            self.state.hour_page = 0
            self.state.failed = False
            self.state.status = (
                "Showing previously retrieved city weather · see download time below"
            )
            return
        self.state.status, self.state.loading, self.state.failed = (
            f"Retrieving weather for {location.name}…",
            True,
            False,
        )
        token = (self.generation, "weather")
        self.workers.submit("main", token, lambda: self.backend.weather(location))

    def retry(self):
        if self.last_action:
            kind, arg = self.last_action
            self.search(arg) if kind == "search" else self.choose(arg, force=True)

    def refresh(self):
        if self.state.bundle:
            self.choose(self.state.bundle.location, force=True)

    def set_tab(self, tab):
        if tab not in ("Today", "Tomorrow", "Next 7 Days"):
            raise ValueError("Unknown tab")
        self.state.tab = tab
        self.state.hour_page = 0
        if self.state.bundle:
            today = local_today(self.state.bundle, self.clock())
            if tab in ("Today", "Tomorrow"):
                self.state.selected_date = today + timedelta(
                    days=int(tab == "Tomorrow")
                )

    def select_day(self, day):
        self.state.selected_date = day
        self.state.tab = "Next 7 Days"
        self.state.hour_page = 0

    def set_unit(self, unit):
        if unit not in ("°C", "°F"):
            raise ValueError("Unknown unit")
        self.state.unit = unit

    def add_current_city(self):
        bundle = self.state.bundle
        if not bundle:
            return
        loc = bundle.location
        if loc not in self.state.cities and len(self.state.cities) >= 3:
            self.state.status = (
                "Three cities are pinned. Remove one before adding another."
            )
            return
        self.state.cities[loc] = LocationWeatherResult(loc, weather=bundle)

    def remove_city(self, location):
        self.state.cities.pop(location, None)
        self.state.city_loading.discard(location)
        self.city_generation[location] = self.city_generation.get(location, 0) + 1
        self.workers.cancel(("city", location))

    def refresh_city(self, location):
        if (
            location not in self.state.cities
            or location in self.state.city_loading
            or not self._allowed()
        ):
            return
        generation = self.city_generation.get(location, 0) + 1
        self.city_generation[location] = generation
        self.state.city_loading.add(location)
        self.workers.submit(
            ("city", location), generation, lambda: self.backend.weather(location)
        )

    def tick_dates(self):
        b = self.state.bundle
        if not b:
            return False
        today = local_today(b, self.clock())
        desired = (
            today + timedelta(days=int(self.state.tab == "Tomorrow"))
            if self.state.tab != "Next 7 Days"
            else self.state.selected_date
        )
        if desired < today or desired > today + timedelta(days=6):
            desired = today
        changed = desired != self.state.selected_date
        self.state.selected_date = desired
        return changed

    def request_icons(self, ids):
        from .components.weather_icon import fetch_icons

        self.icon_pending.update(ids)
        batch = frozenset(self.icon_pending)
        self.workers.submit("icons", 0, lambda: fetch_icons(batch))

    def drain(self):
        if self.closed:
            return False
        changed = False
        while True:
            try:
                scope, token, value, error = self.workers.results.get_nowait()
            except Empty:
                break
            if scope == "main":
                generation, kind = token
                if generation != self.generation:
                    continue
                changed = True
                self.state.loading = False
                if error:
                    self.state.status = str(error)
                    self.state.failed = True
                    self._rate_limit(error)
                elif kind == "search":
                    if len(value) == 1:
                        self.choose(value[0])
                    else:
                        self.state.candidates = tuple(value)
                        self.state.status = (
                            "Choose the matching city, region and country."
                        )
                else:
                    self.state.bundle = value
                    self.state.failed = False
                    self.state.tab = "Today"
                    self.state.selected_date = local_today(value, self.clock())
                    self.state.hour_page = 0
                    self.state.status = "Weather updated · Open-Meteo model data"
                    if value.location in self.state.cities:
                        self.state.cities[value.location] = LocationWeatherResult(
                            value.location, weather=value
                        )
            elif scope == "icons":
                if value:
                    self.icon_results.update(value)
                    self.icon_version += 1
                self.icon_pending.clear()
            elif isinstance(scope, tuple) and scope[0] == "city":
                loc = scope[1]
                if (
                    loc not in self.state.cities
                    or self.city_generation.get(loc) != token
                ):
                    continue
                changed = True
                self.state.city_loading.discard(loc)
                if error:
                    # Preserve a successful older bundle, explicitly paired with failure.
                    previous = self.state.cities[loc].weather
                    self.state.cities[loc] = LocationWeatherResult(loc, previous, error)
                    self._rate_limit(error)
                else:
                    self.state.cities[loc] = LocationWeatherResult(loc, weather=value)
        return changed

    def _rate_limit(self, error):
        if isinstance(error, WeatherRateLimitError):
            self.retry_at = self.tick() + (
                error.retry_after_seconds
                if error.retry_after_seconds is not None
                else 60
            )

            for location in tuple(self.state.city_loading):
                self.workers.cancel(("city", location))
                self.city_generation[location] = (
                    self.city_generation.get(location, 0) + 1
                )
                previous = self.state.cities[location].weather
                self.state.cities[location] = LocationWeatherResult(
                    location, previous, error
                )
            self.state.city_loading.clear()

    def close(self):
        self.closed = True
        self.generation += 1
        self.workers.close()

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
from app.services.cache_service import retrieve, WeatherResult, provenance
from app.services.ip_location_service import IpLocationService


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
    cache_source: str = "network"
    offline: bool = False
    storage_notice: str = ""
    approximate: object = None


class Controller:
    def __init__(
        self,
        backend=None,
        workers=None,
        clock=None,
        tick=monotonic,
        store=None,
        ip_service=None,
    ):
        self.backend = backend or Backend()
        self.store = store
        self.ip_service = ip_service or IpLocationService()
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
        self.state.approximate = None
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
        if (
            saved
            and saved.weather
            and not saved.error
            and not force
            and self.store is None
        ):
            self.state.bundle = saved.weather
            self.state.cache_source = "session cache"
            self.state.offline = False
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
        self.workers.submit(
            "main",
            token,
            lambda: (
                retrieve(self.backend, self.store, location, self.clock(), force)
                if self.store
                else self.backend.weather(location)
            ),
        )

    def detect_location(self, *, consent=False):
        if consent is not True or self.closed:
            return False
        if self.state.loading and self.last_action == ("detect", None):
            return False
        self.invalidate()
        self.last_action = ("detect", None)
        self.state.loading = True
        self.state.failed = False
        self.state.status = "Detecting approximate city · IPWHOIS.IO…"
        self.workers.submit(
            "main",
            (self.generation, "detect"),
            lambda: self.ip_service.detect(consent=True),
        )
        return True

    def retry(self):
        if self.last_action:
            kind, arg = self.last_action
            if kind == "search":
                self.search(arg)
            elif kind == "weather":
                self.choose(arg, force=True)
            else:
                self.state.status = "Choose Detect My Location to give consent again."

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
            ("city", location),
            generation,
            lambda: (
                retrieve(self.backend, self.store, location, self.clock(), True)
                if self.store
                else self.backend.weather(location)
            ),
        )

    def tick_dates(self):
        b = self.state.bundle
        if not b:
            return False
        if self.clock() - b.retrieved_at >= timedelta(minutes=20):
            self.state.cache_source = "stale cache"
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
                elif kind == "detect":
                    self.state.approximate = value
                    self.state.status = (
                        "Approximate location found. Confirm it or search manually."
                    )
                elif kind == "search":
                    if len(value) == 1:
                        self.choose(value[0])
                    else:
                        self.state.candidates = tuple(value)
                        self.state.status = (
                            "Choose the matching city, region and country."
                        )
                else:
                    result = (
                        value
                        if isinstance(value, WeatherResult)
                        else WeatherResult(value)
                    )
                    value = result.bundle
                    self.state.cache_source = result.source
                    self.state.offline = result.offline
                    self.state.storage_notice = result.notice
                    self.state.bundle = value
                    self.state.failed = False
                    self.state.tab = "Today"
                    self.state.selected_date = local_today(value, self.clock())
                    self.state.hour_page = 0
                    self.state.status = provenance(value, result.source, result.offline)
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
                    result = (
                        value
                        if isinstance(value, WeatherResult)
                        else WeatherResult(value)
                    )
                    self.state.cities[loc] = LocationWeatherResult(
                        loc,
                        weather=result.bundle,
                        error=(
                            WeatherProviderError("Cached weather")
                            if result.offline
                            else None
                        ),
                    )
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

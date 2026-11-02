from queue import Queue
from dataclasses import replace
from datetime import timedelta
from threading import Event
import pytest
from app.core.exceptions import (
    LocationNotFoundError,
    WeatherTimeoutError,
    WeatherNetworkError,
    WeatherRateLimitError,
)
from app.ui.controller import Controller, LatestWorkers


class Workers:
    def __init__(self):
        self.pending = {}
        self.results = Queue()
        self.closed = False

    def submit(self, scope, token, action):
        self.pending[scope] = (token, action)

    def cancel(self, scope):
        self.pending.pop(scope, None)

    def finish(self, scope, value=None, error=None):
        token, action = self.pending.pop(scope)
        self.results.put((scope, token, value, error))

    def close(self):
        self.closed = True
        self.pending.clear()


class Backend:
    def search(self, q):
        raise AssertionError("manual worker fixtures should not call backend")

    def weather(self, l):
        raise AssertionError("manual worker fixtures should not call backend")


@pytest.fixture
def controller(now):
    return Controller(Backend(), Workers(), clock=lambda: now, tick=lambda: 100)


def ready(controller, bundle, location):
    controller.choose(location)
    controller.workers.finish("main", bundle)
    controller.drain()
    return controller


def test_search_success(controller, location, bundle):
    controller.search("London")
    assert controller.state.loading
    controller.workers.finish("main", (location,))
    controller.drain()
    assert controller.state.loading and controller.last_action == ("weather", location)
    controller.workers.finish("main", bundle)
    controller.drain()
    assert controller.state.bundle == bundle and not controller.state.loading


@pytest.mark.parametrize("query", ["", "x", "  ", "\nLondon"])
def test_invalid_search(controller, query):
    controller.search(query)
    assert controller.state.failed and not controller.workers.pending


@pytest.mark.parametrize(
    "error",
    [
        LocationNotFoundError("No location"),
        WeatherTimeoutError("Timeout"),
        WeatherNetworkError("Offline"),
    ],
)
def test_failure_retains_previous(controller, bundle, location, error):
    ready(controller, bundle, location)
    controller.search("Other")
    controller.workers.finish("main", error=error)
    controller.drain()
    assert (
        controller.state.bundle is bundle
        and controller.state.failed
        and not controller.state.loading
    )
    controller.retry()
    assert controller.state.loading


def test_ambiguity(controller, location):
    other = replace(location, provider_id=123, country="Canada", country_code="CA")
    controller.search("London")
    controller.workers.finish("main", (location, other))
    controller.drain()
    assert (
        controller.state.candidates == (location, other)
        and not controller.state.loading
    )
    controller.choose(other)
    assert controller.state.candidates == ()


def test_stale_results_and_cancellation(controller, location, bundle):
    controller.search("London")
    old = controller.workers.pending["main"][0]
    controller.search("Paris")
    new = controller.workers.pending["main"][0]
    controller.workers.results.put(("main", old, (location,), None))
    controller.drain()
    assert controller.state.query == "Paris" and controller.state.candidates == ()
    controller.invalidate()
    controller.workers.results.put(("main", new, (location,), None))
    controller.drain()
    assert controller.state.candidates == () and not controller.state.loading
    controller.choose(location)
    old = controller.workers.pending["main"][0]
    controller.search("Tokyo")
    controller.workers.results.put(("main", old, bundle, None))
    controller.drain()
    assert controller.state.bundle is None


def test_rapid_requests_are_bounded(controller):
    for i in range(200):
        controller.search(f"Place {i}")
    assert len(controller.workers.pending) == 1
    token = controller.workers.pending["main"][0]
    controller.search("Place 199")
    assert controller.workers.pending["main"][0] == token


def test_tabs_units_no_fetch(controller, bundle, location, now):
    ready(controller, bundle, location)
    controller.set_tab("Tomorrow")
    assert controller.state.selected_date == now.date() + timedelta(days=1)
    controller.set_unit("°F")
    controller.set_tab("Next 7 Days")
    assert controller.state.unit == "°F" and not controller.workers.pending
    controller.select_day(now.date() + timedelta(days=4))
    assert controller.state.tab == "Next 7 Days"
    controller.set_tab("Today")
    assert controller.state.selected_date == now.date()
    assert bundle.current.temperature_c == 8.4


def test_city_reuse_partial_remove(controller, bundle, location):
    ready(controller, bundle, location)
    controller.add_current_city()
    assert (
        controller.state.cities[location].weather is bundle
        and not controller.workers.pending
    )
    controller.refresh_city(location)
    assert location in controller.state.city_loading
    error = WeatherTimeoutError("Retry later")
    controller.workers.finish(("city", location), error=error)
    controller.drain()
    assert controller.state.cities[location].weather is bundle
    assert controller.state.cities[location].error is error
    controller.refresh_city(location)
    token = controller.workers.pending[("city", location)][0]
    controller.remove_city(location)
    controller.workers.results.put((("city", location), token, bundle, None))
    controller.drain()
    assert not controller.state.cities


def test_city_limit(controller, bundle, location):
    for i in range(4):
        controller.state.bundle = replace(
            bundle, location=replace(location, provider_id=i)
        )
        controller.add_current_city()
    assert len(controller.state.cities) == 3


def test_rate_limit(controller, location):
    controller.search("London")
    controller.workers.finish("main", error=WeatherRateLimitError(120))
    controller.drain()
    controller.choose(location)
    assert not controller.workers.pending and "Retry in" in controller.state.status
    controller.tick = lambda: 221
    controller.choose(location)
    assert controller.state.loading


def test_midnight(controller, bundle, location, now):
    ready(controller, bundle, location)
    controller.clock = lambda: now + timedelta(days=1)
    assert (
        controller.tick_dates()
        and controller.state.selected_date == now.date() + timedelta(days=1)
    )


def test_close_ignores_result(controller, bundle, location):
    controller.choose(location)
    token = controller.workers.pending["main"][0]
    controller.close()
    controller.workers.results.put(("main", token, bundle, None))
    assert (
        not controller.drain()
        and controller.state.bundle is None
        and controller.workers.closed
    )
    controller.search("Paris")
    assert not controller.workers.pending


def test_real_worker_pool_replacement_and_close():
    workers = LatestWorkers()
    release = Event()
    started1 = Event()
    started2 = Event()

    def block(started):
        started.set()
        release.wait(2)

    workers.submit("hold1", 1, lambda: block(started1))
    workers.submit("hold2", 2, lambda: block(started2))
    assert started1.wait(1) and started2.wait(1)
    for i in range(100):
        workers.submit("main", i, lambda: 42)
    assert len(workers.pending) == 1 and workers.pending["main"][0] == 99
    release.set()
    results = [workers.results.get(timeout=2) for _ in range(3)]
    assert ("main", 99, 42, None) in results
    workers.close()
    assert all(not t.is_alive() for t in workers.threads)


def test_city_selection_reuses_bundle_but_refresh_fetches(controller, bundle, location):
    ready(controller, bundle, location)
    controller.add_current_city()
    controller.choose(location)
    assert controller.state.bundle is bundle and not controller.workers.pending
    assert "previously retrieved" in controller.state.status
    controller.refresh()
    assert "main" in controller.workers.pending


def test_repeated_weather_selection_coalesces(controller, location):
    controller.choose(location)
    token = controller.workers.pending["main"][0]
    controller.choose(location)
    assert controller.workers.pending["main"][0] == token


def test_rate_limit_cancels_other_city_work(controller, bundle, location):
    ready(controller, bundle, location)
    controller.add_current_city()
    other = replace(location, provider_id=99)
    controller.state.bundle = replace(bundle, location=other)
    controller.add_current_city()
    controller.refresh_city(location)
    controller.refresh_city(other)
    controller.workers.finish(("city", location), error=WeatherRateLimitError(60))
    controller.drain()
    assert not controller.state.city_loading and not controller.workers.pending
    assert isinstance(controller.state.cities[other].error, WeatherRateLimitError)

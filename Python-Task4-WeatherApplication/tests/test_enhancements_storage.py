import json
import sqlite3
from dataclasses import replace, asdict
from datetime import timedelta
import pytest
from app.storage.local import (
    LocalStore,
    StorageError,
    identity,
    encode,
    decode,
    MAX_CACHE,
)
from app.services.cache_service import retrieve, cache_kind, provenance
from app.core.exceptions import (
    WeatherNetworkError,
    WeatherDataError,
    WeatherRateLimitError,
)
from app.ui.presentation import hour_window, day_slots
from app.ui.controller import Controller
from test_ui_controller import Workers


@pytest.fixture
def store(tmp_path):
    return LocalStore(tmp_path / "skycast.sqlite3")


def test_favorites_persistence_duplicates_and_removal(store, location):
    store.add_favorite(location)
    store.add_favorite(location)
    other = replace(
        location,
        provider_id=2,
        region="Ontario",
        country="Canada",
        country_code="CA",
        latitude=42.98,
        longitude=-81.24,
    )
    store.add_favorite(other)
    reopened = LocalStore(store.path)
    assert reopened.favorites() == ([location, other], 0)
    reopened.remove_favorite(location)
    reopened.remove_favorite(location)
    assert reopened.favorites() == ([other], 0)


def test_corrupt_favorite_skips_without_deletion(store, location):
    store.add_favorite(location)
    with sqlite3.connect(store.path) as con:
        con.execute("INSERT INTO favorites VALUES ('broken','{}','now')")
    assert store.favorites() == ([location], 1)
    with sqlite3.connect(store.path) as con:
        assert con.execute("select count(*) from favorites").fetchone()[0] == 2


def test_corrupt_database_isolated(tmp_path):
    p = tmp_path / "bad.db"
    p.write_text("not sqlite")
    with pytest.raises(StorageError):
        LocalStore(p)
    assert p.read_text() == "not sqlite"


def test_newer_schema_not_reset(store):
    with sqlite3.connect(store.path) as con:
        con.execute("pragma user_version=99")
    with pytest.raises(StorageError):
        LocalStore(store.path)


def test_cache_roundtrip_clear_keeps_favorites(store, bundle, location, now):
    store.add_favorite(location)
    store.save(bundle, now)
    assert store.load(location, now) == bundle
    assert decode(encode(bundle)) == bundle
    store.clear_cache()
    assert store.load(location, now) is None
    assert store.favorites()[0] == [location]


def test_old_write_cannot_replace_new(store, bundle, location, now):
    newer = replace(bundle, retrieved_at=now + timedelta(minutes=1))
    store.save(newer, now + timedelta(minutes=1))
    store.save(bundle, now + timedelta(minutes=2))
    assert store.load(location, now + timedelta(minutes=2)) == newer


@pytest.mark.parametrize("change", [{"schema": 99}, {"bundle": {}}, None])
def test_invalid_cache_records(store, bundle, location, now, change):
    store.save(bundle, now)
    payload = (
        "not-json"
        if change is None
        else json.dumps({**json.loads(encode(bundle)), **change})
    )
    with sqlite3.connect(store.path) as con:
        con.execute("update cache set payload=?", (payload,))
    with pytest.raises(StorageError):
        store.load(location, now)


def test_location_association_and_expiration(store, bundle, location, now):
    store.save(bundle, now)
    assert store.load(replace(location, provider_id=99), now) is None
    assert store.load(location, now + timedelta(days=8)) is None
    assert store.load(location, now - timedelta(seconds=1)) is None
    other = replace(bundle, location=replace(location, name="Wrong city"))
    with sqlite3.connect(store.path) as con:
        con.execute("update cache set payload=?", (encode(other),))
    with pytest.raises(StorageError):
        store.load(location, now)


def test_cache_bound(store, bundle, location, now):
    for i in range(MAX_CACHE + 5):
        store.save(replace(bundle, location=replace(location, provider_id=i)), now)
    with sqlite3.connect(store.path) as con:
        assert con.execute("select count(*) from cache").fetchone()[0] == MAX_CACHE


@pytest.mark.parametrize(
    "minutes,expected",
    [
        (0, "recent cache"),
        (19, "recent cache"),
        (20, "stale cache"),
        (200, "stale cache"),
    ],
)
def test_freshness(bundle, now, minutes, expected):
    assert cache_kind(bundle, now + timedelta(minutes=minutes)) == expected


class Backend:
    def __init__(self, bundle, error=None):
        self.bundle = bundle
        self.error = error
        self.calls = 0

    def weather(self, location):
        self.calls += 1
        if self.error:
            raise self.error
        return self.bundle


def test_recent_cache_and_forced_refresh(store, bundle, location, now):
    store.save(bundle, now)
    backend = Backend(bundle)
    assert retrieve(backend, store, location, now).source == "recent cache"
    assert backend.calls == 0
    assert retrieve(backend, store, location, now, True).source == "network"
    assert backend.calls == 1


def test_offline_fallback_recovery_and_filtering(store, bundle, location, now):
    store.save(bundle, now)
    backend = Backend(bundle, WeatherNetworkError("Offline"))
    later = now + timedelta(days=2)
    result = retrieve(backend, store, location, later)
    assert result.offline and result.source == "stale cache"
    assert "Connection unavailable" in provenance(
        result.bundle, result.source, result.offline
    )
    assert all(
        r.forecast_at > later
        for r in hour_window(result.bundle, later.date(), later).entries
    )
    assert all(d >= later.date() for d, r in day_slots(result.bundle, later))
    backend.error = None
    backend.bundle = replace(bundle, retrieved_at=later)
    result = retrieve(backend, store, location, later, True)
    assert result.source == "network" and not result.offline


@pytest.mark.parametrize("error", [WeatherDataError("bad"), WeatherRateLimitError(60)])
def test_no_malformed_or_rate_limited_cache_success(
    store, bundle, location, now, error
):
    store.save(bundle, now)
    with pytest.raises(type(error)):
        retrieve(Backend(bundle, error), store, location, now, True)
    assert store.load(location, now) == bundle


def test_offline_without_cache_errors(store, bundle, location, now):
    with pytest.raises(WeatherNetworkError):
        retrieve(Backend(bundle, WeatherNetworkError()), store, location, now)


def test_corrupt_cache_does_not_block_online(store, bundle, location, now):
    store.save(bundle, now)
    with sqlite3.connect(store.path) as con:
        con.execute("update cache set payload='bad'")
    result = retrieve(Backend(bundle), store, location, now)
    assert result.source == "network" and result.notice
    assert store.load(location, now) == bundle


def test_controller_cached_state_and_refresh(store, bundle, location, now):
    store.save(bundle, now)
    backend = Backend(bundle)
    workers = Workers()
    c = Controller(backend, workers, clock=lambda: now, store=store)
    c.choose(location)
    result = workers.pending["main"][1]()
    workers.finish("main", result)
    c.drain()
    assert c.state.cache_source == "recent cache" and backend.calls == 0
    c.refresh()
    result = workers.pending["main"][1]()
    workers.finish("main", result)
    c.drain()
    assert c.state.cache_source == "network" and backend.calls == 1
    assert c.state.bundle == bundle


def test_open_display_becomes_stale(bundle, location, now):
    workers = Workers()
    c = Controller(Backend(bundle), workers, clock=lambda: now)
    c.choose(location)
    workers.finish("main", bundle)
    c.drain()
    c.clock = lambda: now + timedelta(minutes=21)
    c.tick_dates()
    assert c.state.cache_source == "stale cache"

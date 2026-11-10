"""Release regressions: hostile metadata and truthful secondary-city snapshots."""

from datetime import timedelta
from dataclasses import replace
import sqlite3
import pytest
from app.providers.http import JsonClient
from app.core.exceptions import WeatherRateLimitError
from app.storage.local import LocalStore, StorageError, identity
from app.services.cache_service import retrieve
from app.ui.controller import Controller
from test_http import Response, Session, URL
from test_ui_controller import Workers


def test_large_retry_header_does_not_crash_controller():
    transport = JsonClient(Session(Response(429, headers={"Retry-After": "9" * 400})))
    with pytest.raises(WeatherRateLimitError) as error:
        transport.get(URL, {})
    c = Controller(workers=Workers(), tick=lambda: 100.0)
    c.search("London")
    c.workers.finish("main", error=error.value)
    c.drain()
    assert c.state.failed and not c.state.loading
    assert 100 <= c.retry_at <= 86500
    c.close()


@pytest.mark.parametrize("header", ["Fri, 31 Dec 9999 23:59:59 GMT", "999999999999"])
def test_retry_delay_bounded(header):
    with pytest.raises(WeatherRateLimitError) as error:
        JsonClient(Session(Response(429, headers={"Retry-After": header}))).get(URL, {})
    assert error.value.retry_after_seconds <= 86400


def test_deep_corrupt_favorite_does_not_crash_ui(tmp_path, location):
    store = LocalStore(tmp_path / "user.db")
    store.add_favorite(location)
    with sqlite3.connect(store.path) as con:
        con.execute("UPDATE favorites SET location=?", ("[" * 9000 + "0" + "]" * 9000,))
    assert store.favorites() == ([], 1)
    with sqlite3.connect(store.path) as con:
        assert con.execute("SELECT count(*) FROM favorites").fetchone()[0] == 1


def test_deep_corrupt_cache_does_not_prevent_online_recovery(tmp_path, bundle, now):
    store = LocalStore(tmp_path / "user.db")
    store.save(bundle, now)
    with sqlite3.connect(store.path) as con:
        con.execute("UPDATE cache SET payload=?", ("[" * 50000 + "0" + "]" * 50000,))
    with pytest.raises(StorageError):
        store.load(bundle.location, now)

    class Backend:
        def weather(self, location):
            return bundle

    result = retrieve(Backend(), store, bundle.location, now)
    assert result.bundle == bundle and result.source == "network"
    assert store.load(bundle.location, now) == bundle


def test_deep_http_json_has_safe_data_error():
    from app.core.exceptions import WeatherDataError

    with pytest.raises(WeatherDataError):
        JsonClient(Session(Response(raw=b"[" * 50000 + b"0" + b"]" * 50000))).get(
            URL, {}
        )

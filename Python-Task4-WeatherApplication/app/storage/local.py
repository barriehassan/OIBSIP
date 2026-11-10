"""Small transactional SQLite store. No connections cross thread boundaries."""

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, date, timezone, timedelta
from app.core.models import (
    Location,
    CurrentWeather,
    HourlyForecast,
    DailyForecast,
    WeatherBundle,
)

SCHEMA = 1
MAX_CACHE = 30
MAX_FAVORITES = 50
MAX_BYTES = 500_000


class StorageError(Exception):
    pass


def app_data_path():
    base = (
        Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
        if os.name == "nt"
        else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    )
    return base / "NOMOLI_FORGE" / "SkyCast" / "skycast.sqlite3"


def identity(location):
    # Include coordinates and country to guard against provider-ID collisions.
    return json.dumps(
        [
            location.provider_id,
            location.country_code,
            location.latitude,
            location.longitude,
        ],
        separators=(",", ":"),
    )


def encode(bundle):
    return json.dumps(
        {"schema": SCHEMA, "bundle": asdict(bundle)},
        default=lambda v: v.isoformat(),
        allow_nan=False,
    )


def decode(payload):
    if not isinstance(payload, str) or len(payload.encode()) > MAX_BYTES:
        raise ValueError("Invalid cache size")
    raw = json.loads(payload)
    if raw["schema"] != SCHEMA:
        raise ValueError("Unsupported cache version")
    b = raw["bundle"]
    if len(b["hourly_forecasts"]) > 300 or len(b["daily_forecasts"]) > 15:
        raise ValueError("Excessive forecast length")
    loc = Location(**b["location"])
    current = dict(b["current"])
    current["observed_at"] = datetime.fromisoformat(current["observed_at"])
    hourly = []
    for r in b["hourly_forecasts"]:
        r = dict(r)
        r["forecast_at"] = datetime.fromisoformat(r["forecast_at"])
        hourly.append(HourlyForecast(**r))
    daily = []
    for r in b["daily_forecasts"]:
        r = dict(r)
        r["date"] = date.fromisoformat(r["date"])
        for f in ("sunrise_at", "sunset_at"):
            r[f] = datetime.fromisoformat(r[f]) if r[f] else None
        daily.append(DailyForecast(**r))
    bundle = WeatherBundle(
        loc,
        CurrentWeather(**current),
        tuple(hourly),
        tuple(daily),
        b["provider"],
        datetime.fromisoformat(b["retrieved_at"]),
        b["timezone"],
        tuple(b["warnings"]),
    )
    times = [r.forecast_at for r in hourly]
    dates = [r.date for r in daily]
    if len(set(times)) != len(times) or len(set(dates)) != len(dates):
        raise ValueError("Duplicate forecast periods")
    return bundle


class LocalStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else app_data_path()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with closing(self.connect()) as con, con:
                version = con.execute("PRAGMA user_version").fetchone()[0]
                if version not in (0, SCHEMA):
                    raise StorageError(
                        "Local data uses a newer format. Weather search remains available."
                    )
                con.execute(
                    "CREATE TABLE IF NOT EXISTS favorites (id TEXT PRIMARY KEY, location TEXT NOT NULL, added TEXT NOT NULL)"
                )
                con.execute(
                    "CREATE TABLE IF NOT EXISTS cache (id TEXT PRIMARY KEY, retrieved REAL NOT NULL, payload TEXT NOT NULL)"
                )
                con.execute(f"PRAGMA user_version={SCHEMA}")
        except (OSError, sqlite3.Error) as exc:
            raise StorageError(
                "Local storage is unavailable. Weather search remains available."
            ) from exc

    def connect(self):
        return sqlite3.connect(self.path, timeout=0.15)

    def _run(self, operation):
        try:
            with closing(self.connect()) as con, con:
                return operation(con)
        except sqlite3.Error as exc:
            raise StorageError(
                "Local data could not be read or saved. Weather search remains available."
            ) from exc

    def add_favorite(self, location):
        if not isinstance(location, Location):
            raise StorageError("Choose a resolved location first.")

        def write(con):
            if (
                con.execute("SELECT COUNT(*) FROM favorites").fetchone()[0]
                >= MAX_FAVORITES
                and not con.execute(
                    "SELECT 1 FROM favorites WHERE id=?", (identity(location),)
                ).fetchone()
            ):
                raise StorageError("Up to 50 favorites can be saved. Remove one first.")
            con.execute(
                "INSERT OR IGNORE INTO favorites VALUES (?,?,?)",
                (
                    identity(location),
                    json.dumps(asdict(location)),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

        self._run(write)

    def favorites(self):
        def read(con):
            result = []
            invalid = 0
            for key, payload in con.execute(
                "SELECT id,location FROM favorites ORDER BY added LIMIT 50"
            ):
                try:
                    if len(payload) > 20000:
                        raise ValueError()
                    location = Location(**json.loads(payload))
                    if identity(location) != key:
                        raise ValueError()
                    result.append(location)
                except (ValueError, TypeError, KeyError, RecursionError):
                    invalid += 1
            return result, invalid

        return self._run(read)

    def remove_favorite(self, location):
        self._run(
            lambda con: con.execute(
                "DELETE FROM favorites WHERE id=?", (identity(location),)
            )
        )

    def save(self, bundle, now):
        payload = encode(bundle)
        # Round-trip validates types/collection limits before writing successful data.
        decode(payload)
        if bundle.retrieved_at > now + timedelta(minutes=5):
            raise StorageError("Future-dated weather was not cached.")

        def write(con):
            con.execute(
                "INSERT INTO cache VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET retrieved=excluded.retrieved,payload=excluded.payload WHERE excluded.retrieved>=cache.retrieved",
                (identity(bundle.location), bundle.retrieved_at.timestamp(), payload),
            )
            con.execute(
                "DELETE FROM cache WHERE retrieved<?",
                ((now - timedelta(days=7)).timestamp(),),
            )
            con.execute(
                "DELETE FROM cache WHERE id NOT IN (SELECT id FROM cache ORDER BY retrieved DESC LIMIT ?)",
                (MAX_CACHE,),
            )

        self._run(write)

    def load(self, location, now):
        row = self._run(
            lambda con: con.execute(
                "SELECT retrieved,payload FROM cache WHERE id=?", (identity(location),)
            ).fetchone()
        )
        if not row:
            return None
        try:
            bundle = decode(row[1])
            if (
                identity(bundle.location) != identity(location)
                or bundle.location != location
                or bundle.retrieved_at.timestamp() != row[0]
            ):
                raise ValueError()
            age = now - bundle.retrieved_at
            if age < timedelta(0) or age > timedelta(days=7):
                return None
            return bundle
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
            raise StorageError(
                "A cached record is invalid; use Refresh to retrieve weather again."
            ) from exc

    def clear_cache(self):
        self._run(lambda con: con.execute("DELETE FROM cache"))

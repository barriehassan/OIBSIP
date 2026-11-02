from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo
from app.core.exceptions import WeatherNetworkError
from app.storage.local import StorageError

FRESH_FOR = timedelta(minutes=20)


@dataclass(frozen=True)
class WeatherResult:
    bundle: object
    source: str = "network"
    offline: bool = False
    notice: str = ""


def cache_kind(bundle, now):
    age = now - bundle.retrieved_at
    return "recent cache" if timedelta(0) <= age < FRESH_FOR else "stale cache"


def provenance(bundle, source, offline=False):
    stamp = bundle.retrieved_at.astimezone(ZoneInfo(bundle.timezone)).strftime(
        "%d %b %H:%M %Z"
    )
    return (
        ("Connection unavailable · " if offline else "")
        + ("Updated" if source == "network" else "Showing " + source)
        + f" · retrieved {stamp}"
    )


def retrieve(backend, store, location, now, force=False):
    cached = None
    notice = ""
    if store:
        try:
            cached = store.load(location, now)
        except StorageError as exc:
            notice = str(exc)
    if cached and not force and cache_kind(cached, now) == "recent cache":
        return WeatherResult(cached, "recent cache", False, notice)
    try:
        bundle = backend.weather(location)
    except WeatherNetworkError:
        if cached:
            return WeatherResult(cached, cache_kind(cached, now), True, notice)
        raise
    if store:
        try:
            store.save(bundle, now)
        except (StorageError, ValueError, TypeError) as exc:
            notice = "Weather retrieved, but the local cache could not be updated."
    return WeatherResult(bundle, "network", False, notice)

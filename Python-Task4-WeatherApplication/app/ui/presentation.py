"""Pure display projections, shared by widgets and deterministic tests."""

from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo
from app.core.forecast_processor import next_six_hours, seven_days
from app.core.exceptions import ForecastUnavailableError
from app.core.unit_converter import celsius_to_fahrenheit
from app.core.validator import number


def temperature(value, unit="°C", decimals=0):
    if value is None:
        return "—"
    if unit not in ("°C", "°F"):
        raise ValueError("Unsupported temperature unit")
    converted = celsius_to_fahrenheit(value) if unit == "°F" else value
    rounded = round(converted, decimals)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.{decimals}f}{unit}"


def location_label(location):
    return ", ".join(
        dict.fromkeys(
            x for x in (location.name, location.region, location.country) if x
        )
    )


def local_today(bundle, now):
    return now.astimezone(ZoneInfo(bundle.timezone)).date()


def day_slots(bundle, now):
    try:
        selection = seven_days(bundle, now)
        return tuple(zip(selection.dates, selection.entries))
    except ForecastUnavailableError:
        today = local_today(bundle, now)
        return tuple((today + timedelta(days=i), None) for i in range(7))


@dataclass(frozen=True)
class HourWindow:
    entries: tuple
    caption: str
    incomplete: bool
    previous: bool = False
    following: bool = False


def hour_window(bundle, selected, now, page=0):
    tz = ZoneInfo(bundle.timezone)
    if selected == local_today(bundle, now):
        try:
            selection = next_six_hours(bundle, now)
            return HourWindow(
                selection.entries, "Next six hours · local time", not selection.complete
            )
        except ForecastUnavailableError:
            return HourWindow((), "Next six hours unavailable", True)
    rows = sorted(
        (
            r
            for r in bundle.hourly_forecasts
            if r.forecast_at.astimezone(tz).date() == selected
        ),
        key=lambda r: r.forecast_at,
    )
    initial = next(
        (i for i, r in enumerate(rows) if r.forecast_at.astimezone(tz).hour >= 6), 0
    )
    start = max(0, min(initial + page * 6, max(0, len(rows) - 1)))
    entries = tuple(rows[start : start + 6])
    gaps = any(
        b.forecast_at - a.forecast_at != timedelta(hours=1)
        for a, b in zip(entries, entries[1:])
    )
    partial = (
        len(entries) < 6
        or gaps
        or any(r.temperature_c is None or r.weather_code is None for r in entries)
    )
    return HourWindow(
        entries,
        selected.strftime("%a %d %b") + " · hourly forecast",
        partial,
        start > 0,
        start + 6 < len(rows),
    )


def local_hour(instant, timezone):
    # UTC offsets disambiguate repeated wall-clock hours in the text detail view.
    return instant.astimezone(ZoneInfo(timezone)).strftime("%d %b %H:%M %z")


def map_rectangle(width, height):
    w = min(width, height * 2)
    h = w / 2
    return ((width - w) / 2, (height - h) / 2, w, h)


def project(latitude, longitude, rectangle):
    number(latitude, minimum=-90, maximum=90)
    number(longitude, minimum=-180, maximum=180)
    x, y, width, height = rectangle
    return x + (longitude + 180) * width / 360, y + (90 - latitude) * height / 180

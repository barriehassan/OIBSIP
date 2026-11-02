"""Pure enhancement projections; no requests or UI mutations."""

from zoneinfo import ZoneInfo
from app.core.unit_converter import celsius_to_fahrenheit
from app.ui.presentation import temperature, hour_window, day_slots


def chart_points(rows, unit, timezone):
    zone = ZoneInfo(timezone)
    unique = {r.forecast_at: r for r in rows}
    return tuple(
        (
            stamp,
            (
                None
                if row.temperature_c is None
                else (
                    celsius_to_fahrenheit(row.temperature_c)
                    if unit == "°F"
                    else row.temperature_c
                )
            ),
            stamp.astimezone(zone).strftime("%d %b %H:%M %z"),
        )
        for stamp, row in sorted(unique.items())
    )


def metrics(bundle, unit, now):
    current = bundle.current
    hours = hour_window(
        bundle, now.astimezone(ZoneInfo(bundle.timezone)).date(), now
    ).entries
    rain = hours[0] if hours else None
    return [
        (
            "◌ Humidity",
            (
                "—"
                if current.humidity_percent is None
                else f"{current.humidity_percent:g}%"
            ),
            "Relative humidity",
        ),
        (
            "↝ Wind",
            (
                "—"
                if current.wind_speed_kmh is None
                else f"{current.wind_speed_kmh:g} km/h"
            ),
            "Wind speed",
        ),
        (
            "♨ Feels like",
            temperature(current.feels_like_c, unit),
            "Apparent temperature",
        ),
        (
            "☂ Rain chance",
            (
                "—"
                if rain is None or rain.precipitation_probability is None
                else f"{rain.precipitation_probability:g}%"
            ),
            (
                rain.forecast_at.astimezone(ZoneInfo(bundle.timezone)).strftime(
                    "%d %b %H:%M %Z forecast"
                )
                if rain
                else "No upcoming hour available"
            ),
        ),
    ]


def solar_text(bundle, selected, now):
    row = next((r for d, r in day_slots(bundle, now) if d == selected), None)

    def display(value):
        if value is None:
            return "Unavailable"
        local = value.astimezone(ZoneInfo(bundle.timezone))
        return (
            local.strftime("%H:%M %Z")
            if local.date() == selected
            else "Unavailable for selected local date"
        )

    sunrise = display(row.sunrise_at if row else None)
    sunset = display(row.sunset_at if row else None)
    return f"{selected:%d %b} · Sunrise {sunrise}   ·   Sunset {sunset}"

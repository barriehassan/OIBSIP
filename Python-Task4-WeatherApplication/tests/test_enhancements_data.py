from dataclasses import replace
from datetime import timedelta, datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import pytest
from app.ui.enhancement_data import chart_points, metrics, solar_text
from app.services.voice_service import speech_text


def test_voice_units_and_actual_values(bundle):
    text = speech_text(bundle, "°C")
    assert "London" in text and "8 degrees Celsius" in text and "Humidity is" in text
    assert "47 degrees Fahrenheit" in speech_text(bundle, "°F")
    assert "Last retrieved conditions" in speech_text(bundle, "°C", True)
    assert speech_text(None) == ""


def test_voice_missing_optional(bundle):
    current = SimpleNamespace(**vars(bundle.current))
    current.description = bundle.current.description
    current.feels_like_c = None
    current.humidity_percent = None
    current.wind_speed_kmh = None
    text = speech_text(SimpleNamespace(**{**vars(bundle), "current": current}))
    assert (
        "feels like" not in text and "Humidity" not in text and "Wind speed" not in text
    )


def test_metrics_real_values_and_rain_period(bundle, now):
    values = metrics(bundle, "°F", now)
    assert values[0][1] == "78%"
    assert values[1][1] == "12.6 km/h"
    assert values[2][1].endswith("°F")
    assert "forecast" in values[3][2] and "%" in values[3][1]


def test_missing_rain_and_expired_hours(bundle, now):
    rows = tuple(
        replace(r, precipitation_probability=None) for r in bundle.hourly_forecasts
    )
    assert metrics(replace(bundle, hourly_forecasts=rows), "°C", now)[3][1] == "—"
    assert (
        metrics(bundle, "°C", now + timedelta(days=30))[3][2]
        == "No upcoming hour available"
    )


def test_chart_order_units_and_empty(bundle):
    rows = bundle.hourly_forecasts[:3]
    points = chart_points(tuple(reversed(rows)), "°F", bundle.timezone)
    assert [x[0] for x in points] == sorted(r.forecast_at for r in rows)
    assert points[0][1] == pytest.approx(rows[0].temperature_c * 1.8 + 32)
    assert chart_points((), "°C", "UTC") == ()
    assert len(chart_points((rows[0],), "°C", "UTC")) == 1
    assert (
        chart_points((replace(rows[0], temperature_c=None),), "°C", "UTC")[0][1] is None
    )


def test_chart_midnight_and_dst_labels(bundle):
    first = replace(
        bundle.hourly_forecasts[0],
        forecast_at=datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc),
    )
    second = replace(first, forecast_at=first.forecast_at + timedelta(hours=1))
    p = chart_points((first, second), "°C", "Europe/London")
    assert p[0][2] != p[1][2] and "+0100" in p[0][2] and "+0000" in p[1][2]
    p = chart_points(
        (replace(first, forecast_at=datetime(2026, 1, 15, 23, tzinfo=timezone.utc)),),
        "°C",
        "Asia/Tokyo",
    )
    assert "16 Jan 08:00" in p[0][2]


def test_solar_missing_and_local_date(bundle, now):
    d = bundle.daily_forecasts[0]
    missing = replace(d, sunrise_at=None, sunset_at=None)
    b = replace(bundle, daily_forecasts=(missing,))
    assert "Sunrise Unavailable" in solar_text(b, d.date, now)
    assert "Sunset Unavailable" in solar_text(b, d.date, now)
    actual = solar_text(bundle, d.date, now)
    if d.sunrise_at:
        assert (
            d.sunrise_at.astimezone(ZoneInfo(bundle.timezone)).strftime("%H:%M")
            in actual
        )


def test_solar_boundary_rejects_wrong_day(bundle, now):
    d = bundle.daily_forecasts[0]
    wrong = datetime.combine(
        d.date - timedelta(days=1), datetime.min.time(), timezone.utc
    )
    b = replace(bundle, daily_forecasts=(replace(d, sunrise_at=wrong),))
    assert "Unavailable for selected local date" in solar_text(b, d.date, now)

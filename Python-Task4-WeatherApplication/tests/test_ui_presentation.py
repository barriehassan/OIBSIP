from dataclasses import replace
from datetime import timedelta
import pytest
from app.ui.presentation import (
    temperature,
    day_slots,
    hour_window,
    project,
    map_rectangle,
    local_hour,
)
from app.core.exceptions import WeatherDataError


@pytest.mark.parametrize(
    "value,c,f",
    [
        (0, "0°C", "32°F"),
        (-40, "-40°C", "-40°F"),
        (None, "—", "—"),
        (8.4, "8°C", "47°F"),
    ],
)
def test_unit_display(value, c, f):
    assert temperature(value) == c and temperature(value, "°F") == f


def test_windows(bundle, now):
    assert len(day_slots(bundle, now)) == 7
    today = hour_window(bundle, now.date(), now)
    tomorrow = hour_window(bundle, now.date() + timedelta(days=1), now)
    assert today.entries[0].forecast_at.hour == 15
    assert tomorrow.entries[0].forecast_at.hour == 6
    assert tomorrow.previous and tomorrow.following
    later = hour_window(bundle, now.date() + timedelta(days=1), now, 1)
    assert later.entries[0].forecast_at.hour == 12
    assert not hour_window(bundle, now.date() + timedelta(days=1), now, 2).following


def test_empty_and_null(bundle, now):
    b = replace(bundle, hourly_forecasts=(), daily_forecasts=())
    assert len(day_slots(b, now)) == 7 and all(r is None for _, r in day_slots(b, now))
    assert not hour_window(b, now.date(), now).entries
    assert hour_window(b, now.date() + timedelta(days=1), now).incomplete


@pytest.mark.parametrize(
    "lat,lon,expected",
    [
        (0, 0, (200, 100)),
        (90, -180, (0, 0)),
        (-90, 180, (400, 200)),
        (45, 90, (300, 50)),
    ],
)
def test_projection(lat, lon, expected):
    assert project(lat, lon, (0, 0, 400, 200)) == expected


@pytest.mark.parametrize("lat,lon", [(91, 0), (0, 181), (float("nan"), 0), (True, 0)])
def test_invalid_projection(lat, lon):
    with pytest.raises(WeatherDataError):
        project(lat, lon, (0, 0, 400, 200))


def test_contained_map():
    assert map_rectangle(1000, 300) == (200, 0, 600, 300)
    assert map_rectangle(300, 300) == (0, 75, 300, 150)


def test_dst_label_offsets(bundle):
    from datetime import datetime, timezone

    a = datetime(2026, 11, 1, 5, tzinfo=timezone.utc)
    b = a + timedelta(hours=1)
    assert "01:00 -0400" in local_hour(a, "America/New_York")
    assert "01:00 -0500" in local_hour(b, "America/New_York")

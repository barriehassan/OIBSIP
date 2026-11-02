"""Explicit partial results. No interpolation, synthetic weather or hidden fetches."""
from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta, timezone
from .models import HourlyForecast, DailyForecast
from .validator import utc, zone
from .exceptions import ForecastUnavailableError, WeatherDataError

@dataclass(frozen=True)
class HourlySelection:
    entries: tuple[HourlyForecast, ...]
    gap_after: tuple[datetime, ...]
    complete: bool

@dataclass(frozen=True)
class DailySelection:
    entries: tuple[DailyForecast | None, ...]
    dates: tuple
    complete: bool

@dataclass(frozen=True)
class RainPoint:
    forecast_at: datetime
    probability_percent: float | None


def next_six_hours(bundle, now):
    now = utc(now)
    indexed = {}
    for row in bundle.hourly_forecasts:
        if row.forecast_at in indexed and indexed[row.forecast_at] != row:
            raise WeatherDataError('Conflicting duplicate forecast entries.')
        indexed[row.forecast_at] = row
    rows = tuple(indexed[t] for t in sorted(indexed) if t > now)[:6]
    if not rows:
        raise ForecastUnavailableError('No upcoming hourly forecast is available.')
    gaps = tuple(a.forecast_at for a, b in zip(rows, rows[1:]) if b.forecast_at - a.forecast_at != timedelta(hours=1))
    complete = (len(rows) == 6 and not gaps and rows[0].forecast_at - now <= timedelta(hours=1)
                and all(r.temperature_c is not None and r.weather_code is not None for r in rows))
    return HourlySelection(rows, gaps, complete)


def seven_days(bundle, now):
    tz = zone(bundle.timezone)
    today = utc(now).astimezone(tz).date()
    dates = tuple(today + timedelta(days=i) for i in range(7))
    indexed = {r.date: r for r in bundle.daily_forecasts}
    if not any(d in indexed for d in dates):
        raise ForecastUnavailableError('No upcoming daily forecast is available.')
    entries = []
    # Provider daily bounds are fixed-offset. Correct extrema on local days whose
    # start/end offsets differ from that at retrieval, using complete hourly data.
    reference_offset = bundle.retrieved_at.astimezone(tz).utcoffset()
    hours = {r.forecast_at: r for r in bundle.hourly_forecasts}
    for d in dates:
        row = indexed.get(d)
        start = datetime.combine(d, time(), tz)
        end = datetime.combine(d + timedelta(days=1), time(), tz)
        period_offset = (timedelta(seconds=row.period_utc_offset_seconds)
                         if row is not None and row.period_utc_offset_seconds is not None else reference_offset)
        if row is not None and (start.utcoffset() != period_offset or end.utcoffset() != period_offset):
            cursor, stop = start.astimezone(timezone.utc), end.astimezone(timezone.utc)
            samples = []
            while cursor < stop:
                samples.append(hours.get(cursor))
                cursor += timedelta(hours=1)
            valid = all(x is not None and x.temperature_c is not None for x in samples)
            temperatures = [x.temperature_c for x in samples] if valid else []
            row = replace(row, temperature_max_c=max(temperatures) if valid else None,
                          temperature_min_c=min(temperatures) if valid else None,
                          weather_code=None, precipitation_probability_max=None,
                          source='hourly-derived local day' if valid else 'incomplete local-day coverage')
        entries.append(row)
    complete = all(r is not None and r.temperature_max_c is not None and r.temperature_min_c is not None and r.weather_code is not None for r in entries)
    return DailySelection(tuple(entries), dates, complete)


def rain_chart(selection):
    return tuple(RainPoint(r.forecast_at, r.precipitation_probability) for r in selection.entries)

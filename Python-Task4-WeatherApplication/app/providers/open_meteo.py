"""Open-Meteo JSON adapter; timestamps always enter the application as UTC."""
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from app.core.models import CurrentWeather, HourlyForecast, DailyForecast, WeatherBundle
from app.core.exceptions import WeatherDataError
from app.core import validator as v
from .http import JsonClient

CURRENT = {'temperature_2m': '°C', 'relative_humidity_2m': '%', 'apparent_temperature': '°C',
           'weather_code': 'wmo code', 'wind_speed_10m': 'km/h', 'is_day': ''}
HOURLY = {'temperature_2m': '°C', 'weather_code': 'wmo code', 'precipitation_probability': '%', 'is_day': ''}
DAILY = {'weather_code': 'wmo code', 'temperature_2m_max': '°C', 'temperature_2m_min': '°C',
         'sunrise': 'unixtime', 'sunset': 'unixtime', 'precipitation_probability_max': '%'}

def instant(value):
    v.number(value, 'timestamp')
    try:
        return datetime.fromtimestamp(value, timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:
        raise WeatherDataError('Invalid weather timestamp.') from exc

def day_flag(value, optional=False):
    if value is None and optional:
        return None
    if type(value) is not int or value not in (0, 1):
        raise WeatherDataError('Invalid day/night flag.')
    return bool(value)

def units(data, name, expected):
    actual = data.get(name + '_units')
    if not isinstance(actual, dict) or actual.get('time') != 'unixtime':
        raise WeatherDataError('Missing or invalid timestamp units.')
    for key, unit in expected.items():
        if key in data[name] and actual.get(key) != unit:
            raise WeatherDataError('Unexpected weather units.')

def series(data, name, expected):
    section = data.get(name)
    if section is None:
        return []
    if not isinstance(section, dict) or not isinstance(section.get('time'), list):
        raise WeatherDataError('Invalid forecast structure.')
    units(data, name, expected)
    times = section['time']
    for field in expected:
        values = section.get(field)
        if field in section and (not isinstance(values, list) or len(values) != len(times)):
            raise WeatherDataError('Forecast arrays have inconsistent lengths.')
    return [dict(time=t, **{field: section[field][i] if field in section else None for field in expected})
            for i, t in enumerate(times)]

def unique_sorted(rows, key):
    indexed = {}
    for row in rows:
        identity = key(row)
        if identity in indexed and indexed[identity] != row:
            raise WeatherDataError('Conflicting duplicate forecast entries.')
        indexed[identity] = row
    return tuple(indexed[k] for k in sorted(indexed))

class OpenMeteoWeather:
    def __init__(self, client=None, *, clock=lambda: datetime.now(timezone.utc)):
        self.client = client if client is not None else JsonClient()
        self.clock = clock

    def get_weather(self, location):
        params = dict(latitude=location.latitude, longitude=location.longitude, timezone='auto',
                      timeformat='unixtime', forecast_days=7, temperature_unit='celsius',
                      wind_speed_unit='kmh', precipitation_unit='mm',
                      current=','.join(CURRENT), hourly=','.join(HOURLY), daily=','.join(DAILY))
        data = self.client.get('https://api.open-meteo.com/v1/forecast', params)
        return self.normalize(data, location, self.clock())

    @staticmethod
    def normalize(data, location, retrieved_at):
        try:
            if not isinstance(data, dict) or data.get('error'):
                raise WeatherDataError('Invalid weather response.')
            tz = data['timezone']
            v.zone(tz)
            offset = v.integer(data['utc_offset_seconds'], 'UTC offset')
            if abs(offset) > 86400:
                raise WeatherDataError('Invalid UTC offset.')
            current = data['current']
            if not isinstance(current, dict):
                raise WeatherDataError('Invalid current conditions.')
            units(data, 'current', CURRENT)
            c = CurrentWeather(instant(current['time']), current['temperature_2m'], current['apparent_temperature'],
                               current['relative_humidity_2m'], current['wind_speed_10m'], current['weather_code'],
                               day_flag(current['is_day']))
            hours = [HourlyForecast(instant(r['time']), r['temperature_2m'], r['weather_code'],
                                    r['precipitation_probability'], day_flag(r['is_day'], True))
                     for r in series(data, 'hourly', HOURLY)]
            # Daily API labels use the request's fixed UTC offset, not a DST-varying conversion.
            days = [DailyForecast((instant(r['time']) + timedelta(seconds=offset)).date(),
                                  r['temperature_2m_max'], r['temperature_2m_min'], r['weather_code'],
                                  instant(r['sunrise']) if r['sunrise'] is not None else None,
                                  instant(r['sunset']) if r['sunset'] is not None else None,
                                  r['precipitation_probability_max'], period_utc_offset_seconds=offset)
                    for r in series(data, 'daily', DAILY)]
            warnings = tuple(f'{name} forecast unavailable' for name, values in (('Hourly', hours), ('Daily', days)) if not values)
            return WeatherBundle(replace(location, timezone=tz), c,
                                 unique_sorted(hours, lambda r: r.forecast_at), unique_sorted(days, lambda r: r.date),
                                 'Open-Meteo', retrieved_at, tz, warnings)
        except (KeyError, TypeError, AttributeError) as exc:
            raise WeatherDataError('Incomplete weather response.') from exc

"""Immutable canonical values: Celsius, km/h, percent, UTC instants."""
from dataclasses import dataclass
from datetime import date, datetime
from . import validator as v
from .condition_mapper import interpret
from .exceptions import WeatherDataError

@dataclass(frozen=True)
class Location:
    provider_id: int
    name: str
    region: str | None
    country: str
    country_code: str
    latitude: float
    longitude: float
    timezone: str

    def __post_init__(self):
        v.integer(self.provider_id, 'location ID')
        for field in ('name', 'country', 'country_code'):
            v.text(getattr(self, field), field)
        if self.region is not None:
            v.text(self.region, 'region')
        if len(self.country_code) != 2 or not self.country_code.isascii() or not self.country_code.isalpha():
            raise WeatherDataError('Invalid country code.')
        v.number(self.latitude, 'latitude', minimum=-90, maximum=90)
        v.number(self.longitude, 'longitude', minimum=-180, maximum=180)
        v.zone(self.timezone)

class ConditionFields:
    @property
    def description(self):
        return interpret(self.weather_code).description

    @property
    def category(self):
        return interpret(self.weather_code).category

    @property
    def icon_id(self):
        return interpret(self.weather_code, getattr(self, 'is_day', True)).icon_id

@dataclass(frozen=True)
class CurrentWeather(ConditionFields):
    observed_at: datetime
    temperature_c: float
    feels_like_c: float
    humidity_percent: float
    wind_speed_kmh: float
    weather_code: int
    is_day: bool

    def __post_init__(self):
        object.__setattr__(self, 'observed_at', v.utc(self.observed_at))
        for field in ('temperature_c', 'feels_like_c'):
            v.number(getattr(self, field), field)
        v.number(self.humidity_percent, 'humidity', minimum=0, maximum=100)
        v.number(self.wind_speed_kmh, 'wind', minimum=0)
        v.integer(self.weather_code)
        if type(self.is_day) is not bool:
            raise WeatherDataError('Invalid day/night flag.')

@dataclass(frozen=True)
class HourlyForecast(ConditionFields):
    forecast_at: datetime
    temperature_c: float | None
    weather_code: int | None
    precipitation_probability: float | None = None
    is_day: bool | None = None

    def __post_init__(self):
        object.__setattr__(self, 'forecast_at', v.utc(self.forecast_at))
        v.number(self.temperature_c, 'temperature', optional=True)
        v.integer(self.weather_code, optional=True)
        v.number(self.precipitation_probability, 'probability', minimum=0, maximum=100, optional=True)
        if self.is_day is not None and type(self.is_day) is not bool:
            raise WeatherDataError('Invalid day/night flag.')

@dataclass(frozen=True)
class DailyForecast(ConditionFields):
    date: date
    temperature_max_c: float | None
    temperature_min_c: float | None
    weather_code: int | None
    sunrise_at: datetime | None = None
    sunset_at: datetime | None = None
    precipitation_probability_max: float | None = None
    source: str = 'provider daily (fixed-offset period)'
    period_utc_offset_seconds: int | None = None

    def __post_init__(self):
        if self.period_utc_offset_seconds is not None:
            v.integer(self.period_utc_offset_seconds, 'daily UTC offset')
            v.number(self.period_utc_offset_seconds, minimum=-86400, maximum=86400)
        if type(self.date) is not date:
            raise WeatherDataError('Invalid forecast date.')
        for field in ('temperature_max_c', 'temperature_min_c'):
            v.number(getattr(self, field), field, optional=True)
        if self.temperature_min_c is not None and self.temperature_max_c is not None and self.temperature_min_c > self.temperature_max_c:
            raise WeatherDataError('Daily minimum exceeds maximum.')
        v.integer(self.weather_code, optional=True)
        v.number(self.precipitation_probability_max, 'probability', minimum=0, maximum=100, optional=True)
        for field in ('sunrise_at', 'sunset_at'):
            if getattr(self, field) is not None:
                object.__setattr__(self, field, v.utc(getattr(self, field)))

@dataclass(frozen=True)
class WeatherBundle:
    location: Location
    current: CurrentWeather
    hourly_forecasts: tuple[HourlyForecast, ...]
    daily_forecasts: tuple[DailyForecast, ...]
    provider: str
    retrieved_at: datetime
    timezone: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.location, Location) or not isinstance(self.current, CurrentWeather):
            raise WeatherDataError('Invalid normalized weather.')
        v.zone(self.timezone)
        if self.location.timezone != self.timezone:
            raise WeatherDataError('Inconsistent location timezone.')
        v.text(self.provider)
        object.__setattr__(self, 'retrieved_at', v.utc(self.retrieved_at))
        for field, kind in (('hourly_forecasts', HourlyForecast), ('daily_forecasts', DailyForecast), ('warnings', str)):
            values = tuple(getattr(self, field))
            if not all(isinstance(x, kind) for x in values):
                raise WeatherDataError('Invalid forecast collection.')
            object.__setattr__(self, field, values)

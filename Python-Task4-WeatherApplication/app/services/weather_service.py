from dataclasses import dataclass
from datetime import datetime, timezone
from app.core.models import Location, WeatherBundle
from app.core.exceptions import SkyCastError, LocationValidationError, WeatherDataError, WeatherRateLimitError
from app.core.forecast_processor import next_six_hours, seven_days, rain_chart

@dataclass(frozen=True)
class LocationWeatherResult:
    location: Location
    weather: WeatherBundle | None = None
    error: SkyCastError | None = None

@dataclass(frozen=True)
class MapMarker:
    location: Location
    temperature_c: float | None
    icon_id: str
    observed_at: datetime | None
    error_message: str | None

class WeatherService:
    """Call get_weather once, then pass its bundle to all dashboard accessors.

    Synchronous and worker-ready. Use one service/session per worker; no cache.
    """
    def __init__(self, provider, *, clock=lambda: datetime.now(timezone.utc)):
        self.provider, self.clock = provider, clock

    def get_weather(self, location):
        if not isinstance(location, Location):
            raise LocationValidationError('Choose a resolved location first.')
        bundle = self.provider.get_weather(location)
        # Returned timezone may be more authoritative; identity/coordinates must remain unchanged.
        if (bundle.location.provider_id, bundle.location.latitude, bundle.location.longitude) != (location.provider_id, location.latitude, location.longitude):
            raise WeatherDataError('Weather does not match the requested location.')
        return bundle

    def get_current_weather(self, bundle):
        return bundle.current

    def get_hourly_forecast(self, bundle):
        return next_six_hours(bundle, self.clock())

    def get_daily_forecast(self, bundle):
        return seven_days(bundle, self.clock())

    def get_rain_chart(self, bundle):
        return rain_chart(self.get_hourly_forecast(bundle))

    def get_many(self, locations):
        locations = tuple(locations)
        if len(locations) > 10 or not all(isinstance(x, Location) for x in locations):
            raise LocationValidationError('Select at most ten resolved locations.')
        results, completed, rate_limit = [], {}, None
        for location in locations:
            if location not in completed:
                try:
                    if rate_limit is not None:
                        raise rate_limit
                    completed[location] = LocationWeatherResult(location, self.get_weather(location))
                except SkyCastError as exc:
                    completed[location] = LocationWeatherResult(location, error=exc)
                    if isinstance(exc, WeatherRateLimitError):
                        rate_limit = exc
            results.append(completed[location])
        return tuple(results)

    @staticmethod
    def map_marker(result):
        current = result.weather.current if result.weather else None
        return MapMarker(result.location, current.temperature_c if current else None,
                         current.icon_id if current else 'unknown', current.observed_at if current else None,
                         str(result.error) if result.error else None)

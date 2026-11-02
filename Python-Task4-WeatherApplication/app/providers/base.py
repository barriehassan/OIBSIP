from typing import Protocol
from app.core.models import Location, WeatherBundle

class WeatherProvider(Protocol):
    def get_weather(self, location: Location) -> WeatherBundle: ...

class GeocodingProvider(Protocol):
    def search_locations(self, query: str, country_code: str | None = None) -> tuple[Location, ...]: ...

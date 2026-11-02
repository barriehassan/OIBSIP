"""WMO interpretation and semantic OpenWeather icon identifiers, not images."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Condition:
    description: str
    category: str
    icon_id: str


_CODES = {
    0: ("Clear sky", "clear", "01"),
    1: ("Mainly clear", "mainly_clear", "02"),
    2: ("Partly cloudy", "partly_cloudy", "03"),
    3: ("Overcast", "cloudy", "04"),
    45: ("Fog", "fog", "50"), 48: ("Depositing rime fog", "fog", "50"),
    51: ("Light drizzle", "drizzle", "09"), 53: ("Moderate drizzle", "drizzle", "09"),
    55: ("Dense drizzle", "drizzle", "09"),
    56: ("Light freezing drizzle", "freezing_drizzle", "09"),
    57: ("Dense freezing drizzle", "freezing_drizzle", "09"),
    61: ("Slight rain", "rain", "10"), 63: ("Moderate rain", "rain", "10"),
    65: ("Heavy rain", "rain", "10"),
    66: ("Light freezing rain", "freezing_rain", "10"),
    67: ("Heavy freezing rain", "freezing_rain", "10"),
    71: ("Slight snow", "snow", "13"), 73: ("Moderate snow", "snow", "13"),
    75: ("Heavy snow", "snow", "13"), 77: ("Snow grains", "snow", "13"),
    80: ("Slight rain showers", "showers", "09"),
    81: ("Moderate rain showers", "showers", "09"),
    82: ("Violent rain showers", "showers", "09"),
    85: ("Slight snow showers", "snow", "13"), 86: ("Heavy snow showers", "snow", "13"),
    95: ("Thunderstorm", "thunderstorm", "11"),
    96: ("Thunderstorm with slight hail", "thunderstorm", "11"),
    99: ("Thunderstorm with heavy hail", "thunderstorm", "11"),
}


def interpret(code, is_day=None):
    if type(code) is not int or code not in _CODES:
        return Condition("Unknown conditions", "unknown", "unknown")
    description, category, family = _CODES[code]
    # Unknown solar state is explicit; do not invent daytime/nighttime.
    suffix = "d" if is_day is True else "n" if is_day is False else ""
    return Condition(description, category, family + suffix if suffix else "unknown")

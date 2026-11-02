"""Shared input and model validation. No provider-specific field names."""
from datetime import datetime, timezone
from math import isfinite
import unicodedata
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .exceptions import LocationValidationError, WeatherDataError


def number(value, label="value", *, minimum=None, maximum=None, optional=False):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise WeatherDataError(f"Invalid numeric {label}.")
    try:
        valid = isfinite(value)
    except (OverflowError, TypeError):
        valid = False
    if not valid or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise WeatherDataError(f"Invalid numeric {label}.")
    return float(value)


def integer(value, label="code", *, optional=False):
    if value is None and optional:
        return None
    if type(value) is not int:
        raise WeatherDataError(f"Invalid {label}.")
    return value


def text(value, label="text"):
    if not isinstance(value, str) or not value.strip() or any(unicodedata.category(c).startswith("C") for c in value):
        raise WeatherDataError(f"Invalid {label}.")
    return value.strip()


def zone(name):
    try:
        return ZoneInfo(text(name, "timezone"))
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise WeatherDataError("A valid IANA timezone is required. Check installed tzdata.") from exc


def utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise WeatherDataError("A timezone-aware timestamp is required.")
    return value.astimezone(timezone.utc)


def normalize_query(query):
    if not isinstance(query, str):
        raise LocationValidationError("Enter a city or postal code.")
    if any(unicodedata.category(c).startswith("C") for c in query):
        raise LocationValidationError("The search contains unsupported control characters.")
    query = " ".join(unicodedata.normalize("NFC", query).split())
    if len(query) > 120 or len(query.split(",", 1)[0].strip()) < 2 or not any(c.isalnum() for c in query):
        raise LocationValidationError("Enter a city or postal code of 2–120 characters.")
    return query


def country_filter(value):
    if value is None:
        return None
    if not isinstance(value, str) or len(value.strip()) != 2 or not value.strip().isascii() or not value.strip().isalpha():
        raise LocationValidationError("Use a two-letter country code.")
    return value.strip().upper()

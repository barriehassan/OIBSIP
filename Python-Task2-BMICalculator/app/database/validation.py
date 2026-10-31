"""Shared persistence boundary validation and canonical UTC timestamps."""
from datetime import datetime, timezone
from app.core.validator import ValidationError

def identifier(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= 9223372036854775807:
        raise ValidationError("ID must be a positive supported integer.")
    return value

def profile_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Please enter a profile name.")
    value = value.strip()
    if len(value) > 100 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValidationError("Profile name must contain at most 100 characters and no control characters.")
    return value

def utc_timestamp(value: datetime | None = None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValidationError("Measurement time must be a timezone-aware datetime.")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")

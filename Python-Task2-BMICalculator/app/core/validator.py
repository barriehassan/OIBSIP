"""Input parsing and application-supported measurement limits."""
import math

class ValidationError(ValueError):
    """A controlled, user-readable invalid-input error."""

# Product support limits, inclusive; these are not medical thresholds.
WEIGHT_LIMITS = (1.0, 500.0)
HEIGHT_LIMITS = (0.3, 2.75)

def positive_number(value: object, label: str, *, allow_string: bool = False) -> float:
    """Normalize a positive finite int/float; optionally parse interactive text."""
    if isinstance(value, str) and allow_string:
        if not value.strip():
            raise ValidationError(f"Please enter your {label.lower()}.")
        try:
            value = float(value)
        except ValueError as exc:
            raise ValidationError(f"{label} must be a valid number.") from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{label} must be a valid number.")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValidationError(f"{label} must be a finite number.") from exc
    if not math.isfinite(number):
        raise ValidationError(f"{label} must be a finite number.")
    if number <= 0:
        raise ValidationError(f"{label} must be greater than zero.")
    return number

def _measurement(value: object, label: str, limits: tuple[float, float], unit: str) -> float:
    number = positive_number(value, label, allow_string=True)
    if not limits[0] <= number <= limits[1]:
        raise ValidationError(f"{label} must be between {limits[0]:g} and {limits[1]:g} {unit} (application-supported range).")
    return number

def validate_weight(value: object) -> float:
    """Parse weight in kilograms within the inclusive product support range."""
    return _measurement(value, "Weight", WEIGHT_LIMITS, "kg")

def validate_height(value: object) -> float:
    """Parse height in metres within the inclusive product support range."""
    return _measurement(value, "Height", HEIGHT_LIMITS, "metres")

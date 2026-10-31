"""Pure conversions using exact international unit definitions."""
from .validator import ValidationError, positive_number

KG_PER_POUND = 0.45359237
METRES_PER_INCH = 0.0254
METRES_PER_CENTIMETRE = 0.01
INCHES_PER_FOOT = 12

def pounds_to_kilograms(pounds: float) -> float:
    """Convert positive finite pounds using 1 lb = 0.45359237 kg."""
    return positive_number(positive_number(pounds, "Pounds") * KG_PER_POUND, "Kilograms")

def inches_to_metres(inches: float) -> float:
    """Convert positive finite inches using 1 in = 0.0254 m."""
    return positive_number(positive_number(inches, "Inches") * METRES_PER_INCH, "Metres")

def centimetres_to_metres(centimetres: float) -> float:
    """Convert positive finite centimetres using 1 cm = 0.01 m."""
    return positive_number(positive_number(centimetres, "Centimetres") * METRES_PER_CENTIMETRE, "Metres")

def feet_inches_to_metres(feet: int, inches: float = 0) -> float:
    """Convert whole nonnegative feet and inches in [0, 12); total must be positive."""
    if isinstance(feet, bool) or not isinstance(feet, int) or feet < 0:
        raise ValidationError("Feet must be a nonnegative whole number.")
    if isinstance(inches, bool) or not isinstance(inches, (int, float)):
        raise ValidationError("Inches must be a valid number.")
    if not 0 <= inches < INCHES_PER_FOOT:
        raise ValidationError("Inches must be between zero and less than 12.")
    return inches_to_metres(feet * INCHES_PER_FOOT + inches)

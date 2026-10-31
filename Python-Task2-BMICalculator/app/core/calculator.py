"""Reusable calculation, formatting and result construction."""
from typing import TYPE_CHECKING
from .validator import positive_number, validate_height, validate_weight

if TYPE_CHECKING:
    from .models import BMIResult

def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Return unrounded float BMI from positive finite numeric kg and metres.

    Physical positivity is enforced here; product support limits are enforced
    by interactive validators and BMIResult. Strings and booleans are rejected.
    """
    weight = positive_number(weight_kg, "Weight")
    height = positive_number(height_m, "Height")
    # Sequential division avoids underflow of height squared to zero.
    result = weight / height / height
    return positive_number(result, "Calculated BMI")

def format_bmi(bmi: float) -> str:
    """Format a valid BMI to two decimal places for display only."""
    return f"{positive_number(bmi, 'BMI'):.2f}"

def create_result(weight_kg: object, height_m: object) -> "BMIResult":
    """Parse interactive measurements and return a consistent immutable result."""
    from .models import BMIResult
    return BMIResult(validate_weight(weight_kg), validate_height(height_m))

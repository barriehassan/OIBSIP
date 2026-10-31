"""Immutable domain result without infrastructure dependencies."""
from dataclasses import dataclass, field
from .calculator import calculate_bmi, format_bmi
from .classification import BMICategory, classify_bmi
from .validator import validate_height, validate_weight

@dataclass(frozen=True)
class BMIResult:
    """Derived fields cannot be supplied independently or become inconsistent."""
    weight_kg: float
    height_m: float
    bmi_value: float = field(init=False)
    category: BMICategory = field(init=False)

    def __post_init__(self) -> None:
        weight = validate_weight(self.weight_kg)
        height = validate_height(self.height_m)
        value = calculate_bmi(weight, height)
        object.__setattr__(self, "weight_kg", weight)
        object.__setattr__(self, "height_m", height)
        object.__setattr__(self, "bmi_value", value)
        object.__setattr__(self, "category", classify_bmi(value))

    @property
    def formatted_bmi(self) -> str:
        """Two-decimal display; stored value remains unrounded."""
        return format_bmi(self.bmi_value)

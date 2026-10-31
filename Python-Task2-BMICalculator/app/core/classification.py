"""Pure adult BMI classification and separate presentation metadata."""
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from .validator import positive_number

class BMICategory(str, Enum):
    UNDERWEIGHT = "Underweight"
    NORMAL = "Normal"
    OVERWEIGHT = "Overweight"
    OBESE = "Obese"

@dataclass(frozen=True)
class CategoryMetadata:
    name: str
    colour: str
    explanation: str

CATEGORY_METADATA = MappingProxyType({
    BMICategory.UNDERWEIGHT: CategoryMetadata("Underweight", "#60A5FA", "BMI is below the standard adult reference range."),
    BMICategory.NORMAL: CategoryMetadata("Normal", "#34D399", "BMI is within the standard adult reference range."),
    BMICategory.OVERWEIGHT: CategoryMetadata("Overweight", "#FBBF24", "BMI is above the standard adult reference range."),
    BMICategory.OBESE: CategoryMetadata("Obese", "#FB7185", "BMI is in the highest of these four adult reference categories."),
})

def classify_bmi(bmi: float) -> BMICategory:
    """Classify the original positive finite value without rounding."""
    value = positive_number(bmi, "BMI")
    if value < 18.5:
        return BMICategory.UNDERWEIGHT
    if value < 25:
        return BMICategory.NORMAL
    if value < 30:
        return BMICategory.OVERWEIGHT
    return BMICategory.OBESE

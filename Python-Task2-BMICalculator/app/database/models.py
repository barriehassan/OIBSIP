"""Immutable persistence and comparison values."""
from dataclasses import dataclass
from app.core.classification import BMICategory
from app.core.calculator import format_bmi

@dataclass(frozen=True)
class Profile:
    id: int
    name: str
    created_at: str

@dataclass(frozen=True)
class Measurement:
    id: int
    profile_id: int
    weight_kg: float
    height_m: float
    bmi_value: float
    category: BMICategory
    measured_at: str

    @property
    def formatted_bmi(self) -> str:
        return format_bmi(self.bmi_value)

@dataclass(frozen=True)
class MeasurementComparison:
    previous: Measurement
    latest: Measurement
    weight_change: float
    bmi_change: float

@dataclass(frozen=True)
class DeletionPreview:
    profile: Profile
    measurement_count: int

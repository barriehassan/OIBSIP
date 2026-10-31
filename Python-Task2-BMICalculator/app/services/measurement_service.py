"""Validate and calculate through the established Task 03 entry point."""
from datetime import datetime
from app.core.calculator import create_result
from app.database.measurement_repository import MeasurementRepository
from app.database.models import Measurement

class MeasurementService:
    def __init__(self, measurements: MeasurementRepository):
        self.measurements = measurements

    def save(self, profile_id: int, weight_kg: object, height_m: object,
             measured_at: datetime | None = None) -> Measurement:
        """Accept raw measurements only; BMI/category cannot be supplied."""
        result = create_result(weight_kg, height_m)
        return self.measurements.save(profile_id, result, measured_at)

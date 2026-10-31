"""Profile-isolated historical values, without chart rendering or health advice."""
from app.database.measurement_repository import MeasurementRepository
from app.database.models import Measurement, MeasurementComparison

class HistoryService:
    def __init__(self, measurements: MeasurementRepository):
        self.measurements = measurements

    def history(self, profile_id: int, limit: int | None = None) -> list[Measurement]:
        return self.measurements.history(profile_id, limit)

    def latest(self, profile_id: int) -> Measurement | None:
        return self.measurements.latest(profile_id)

    def previous(self, profile_id: int) -> Measurement | None:
        records = self.history(profile_id, 2)
        return records[-2] if len(records) == 2 else None

    def comparison(self, profile_id: int) -> MeasurementComparison | None:
        records = self.history(profile_id, 2)
        if len(records) < 2:
            return None
        previous, latest = records
        return MeasurementComparison(previous, latest, latest.weight_kg - previous.weight_kg,
                                     latest.bmi_value - previous.bmi_value)

    def chart_data(self, profile_id: int) -> list[tuple[str, float, float]]:
        """Ordered (UTC timestamp, weight kg, unrounded BMI) points."""
        return [(r.measured_at, r.weight_kg, r.bmi_value) for r in self.history(profile_id)]

    def count(self, profile_id: int) -> int:
        return self.measurements.count(profile_id)

    def get(self, profile_id: int, record_id: int) -> Measurement:
        return self.measurements.get(profile_id, record_id)

    def delete(self, profile_id: int, record_id: int) -> None:
        self.measurements.delete(profile_id, record_id)

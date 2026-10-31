"""Testable desktop state and service coordination, independent of Tk."""
from dataclasses import dataclass
from datetime import datetime
from app.core.calculator import create_result
from app.core.conversions import centimetres_to_metres
from app.core.models import BMIResult
from app.core.validator import ValidationError, positive_number
from app.database.models import Measurement, Profile
from app.services.profile_service import ProfileService
from app.services.measurement_service import MeasurementService
from app.services.history_service import HistoryService

@dataclass(frozen=True)
class Summary:
    latest: Measurement | None
    count: int
    weight_change: float | None
    first_weight: float | None

class UIController:
    """One window's selected profile and explicit calculate/save lifecycle."""
    def __init__(self, profiles: ProfileService, measurements: MeasurementService, history: HistoryService):
        self.profiles = profiles
        self.measurements = measurements
        self.history = history
        self.profile_id: int | None = None
        self.result: BMIResult | None = None
        self.saved: Measurement | None = None
        self.calculated_at: datetime | None = None

    def invalidate(self) -> None:
        """Input edits or profile switches invalidate the unsaved calculation."""
        self.result = None
        self.saved = None
        self.calculated_at = None

    def select(self, profile_id: int | None) -> None:
        if profile_id is not None:
            self.profiles.select(profile_id)
        self.profile_id = profile_id
        self.invalidate()

    def calculate(self, weight: object, height_cm: object) -> BMIResult:
        self.invalidate()
        height = positive_number(height_cm, "Height", allow_string=True)
        self.result = create_result(weight, centimetres_to_metres(height))
        from datetime import timezone
        self.calculated_at = datetime.now(timezone.utc)
        return self.result

    def save(self) -> Measurement:
        if self.profile_id is None:
            raise ValidationError("Select or create a profile before saving your result.")
        if self.result is None:
            raise ValidationError("Calculate your BMI before saving.")
        if self.saved is not None:
            raise ValidationError("This result is already saved. Calculate a new measurement to save again.")
        self.saved = self.measurements.save(self.profile_id, self.result.weight_kg,
                                            self.result.height_m, self.calculated_at)
        return self.saved

    def create_profile(self, name: str) -> Profile:
        profile = self.profiles.create(name)
        self.select(profile.id)
        return profile

    def rename_profile(self, name: str) -> Profile:
        if self.profile_id is None:
            raise ValidationError("Select a profile first.")
        return self.profiles.rename(self.profile_id, name)

    def delete_profile(self, *, confirmed: bool = False) -> None:
        if self.profile_id is None:
            raise ValidationError("Select a profile first.")
        self.profiles.delete(self.profile_id, confirmed=confirmed)
        self.select(None)

    def summary(self) -> Summary:
        if self.profile_id is None:
            return Summary(None, 0, None, None)
        records = self.history.history(self.profile_id)
        if not records:
            return Summary(None, 0, None, None)
        return Summary(records[-1], len(records),
                       records[-1].weight_kg-records[0].weight_kg if len(records)>1 else None,
                       records[0].weight_kg)

    def trend_points(self) -> list[tuple[str, float, float]]:
        return [] if self.profile_id is None else self.history.chart_data(self.profile_id)

"""Profile-scoped measurement queries; no BMI formula lives here."""
from datetime import datetime
from app.core.calculator import create_result
from app.core.classification import BMICategory
from app.core.models import BMIResult
from app.core.validator import ValidationError
from .connection import Database
from .models import Measurement
from .errors import ProfileNotFound, MeasurementNotFound
from .validation import identifier, utc_timestamp

def _measurement(row) -> Measurement:
    data = dict(row)
    data["category"] = BMICategory(data["category"])
    return Measurement(**data)

class MeasurementRepository:
    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _profile(c, profile_id: int) -> None:
        identifier(profile_id)
        if c.execute("SELECT id FROM profiles WHERE id=?", (profile_id,)).fetchone() is None:
            raise ProfileNotFound("Profile not found.")

    def save(self, profile_id: int, result: BMIResult, measured_at: datetime | None = None) -> Measurement:
        if not isinstance(result, BMIResult):
            raise ValidationError("A validated BMI result is required.")
        # Validate consistency even if a caller bypassed the frozen dataclass.
        expected = create_result(result.weight_kg, result.height_m)
        if result != expected:
            raise ValidationError("BMI result is inconsistent with its measurements.")
        timestamp = utc_timestamp(measured_at)
        with self.database.connection(write=True) as c:
            self._profile(c, profile_id)
            cursor = c.execute("""INSERT INTO bmi_records(profile_id,weight_kg,height_m,bmi_value,category,measured_at)
                VALUES (?,?,?,?,?,?)""", (profile_id, result.weight_kg, result.height_m, result.bmi_value, result.category.value, timestamp))
            return _measurement(c.execute("SELECT * FROM bmi_records WHERE id=?", (cursor.lastrowid,)).fetchone())

    def history(self, profile_id: int, limit: int | None = None) -> list[Measurement]:
        """Return chronological records; limit selects the newest N, still ascending."""
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 9223372036854775807):
            raise ValidationError("History limit must be a positive supported integer.")
        with self.database.connection() as c:
            self._profile(c, profile_id)
            if limit is None:
                rows = c.execute("SELECT * FROM bmi_records WHERE profile_id=? ORDER BY measured_at,id", (profile_id,)).fetchall()
            else:
                rows = c.execute("SELECT * FROM bmi_records WHERE profile_id=? ORDER BY measured_at DESC,id DESC LIMIT ?", (profile_id, limit)).fetchall()[::-1]
            return [_measurement(row) for row in rows]

    def latest(self, profile_id: int) -> Measurement | None:
        rows = self.history(profile_id, 1)
        return rows[0] if rows else None

    def count(self, profile_id: int) -> int:
        with self.database.connection() as c:
            self._profile(c, profile_id)
            return c.execute("SELECT count(*) FROM bmi_records WHERE profile_id=?", (profile_id,)).fetchone()[0]

    def get(self, profile_id: int, record_id: int) -> Measurement:
        identifier(record_id)
        with self.database.connection() as c:
            self._profile(c, profile_id)
            row = c.execute("SELECT * FROM bmi_records WHERE profile_id=? AND id=?", (profile_id,record_id)).fetchone()
            if row is None:
                raise MeasurementNotFound("Measurement not found for this profile.")
            return _measurement(row)

    def delete(self, profile_id: int, record_id: int) -> None:
        identifier(record_id)
        with self.database.connection(write=True) as c:
            self._profile(c, profile_id)
            if c.execute("DELETE FROM bmi_records WHERE profile_id=? AND id=?", (profile_id,record_id)).rowcount != 1:
                raise MeasurementNotFound("Measurement not found for this profile.")

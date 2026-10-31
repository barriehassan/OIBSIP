"""Local profile operations, without authentication or global selection state."""
from app.database.profile_repository import ProfileRepository
from app.database.measurement_repository import MeasurementRepository
from app.database.models import Profile, DeletionPreview
from app.core.validator import ValidationError

class ProfileService:
    def __init__(self, profiles: ProfileRepository, measurements: MeasurementRepository):
        self.profiles = profiles
        self.measurements = measurements

    def create(self, name: str) -> Profile:
        return self.profiles.create(name)

    def list(self) -> list[Profile]:
        return self.profiles.list()

    def get(self, profile_id: int) -> Profile:
        return self.profiles.get(profile_id)

    def select(self, profile_id: int) -> Profile:
        """Resolve selection; future GUI owns selected-profile state."""
        return self.get(profile_id)

    def rename(self, profile_id: int, name: str) -> Profile:
        return self.profiles.rename(profile_id, name)

    def deletion_preview(self, profile_id: int) -> DeletionPreview:
        """Advisory preview; counts may change before a confirmed deletion."""
        return DeletionPreview(self.get(profile_id), self.measurements.count(profile_id))

    def delete(self, profile_id: int, *, confirmed: bool = False) -> None:
        if confirmed is not True:
            raise ValidationError("Confirm profile deletion and removal of all its measurements.")
        self.profiles.delete(profile_id)

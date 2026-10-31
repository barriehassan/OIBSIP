import pytest
from app.database.connection import Database
from app.database.profile_repository import ProfileRepository
from app.database.measurement_repository import MeasurementRepository
from app.services.profile_service import ProfileService
from app.services.measurement_service import MeasurementService
from app.services.history_service import HistoryService

@pytest.fixture
def storage(tmp_path):
    db = Database(tmp_path / "data" / "test.sqlite3")
    profiles, records = ProfileRepository(db), MeasurementRepository(db)
    return db, ProfileService(profiles, records), MeasurementService(records), HistoryService(records)

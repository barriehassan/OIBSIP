"""Compose repositories/services without side effects on import."""
from pathlib import Path
from app.database.connection import Database
from app.database.profile_repository import ProfileRepository
from app.database.measurement_repository import MeasurementRepository
from app.services.profile_service import ProfileService
from app.services.measurement_service import MeasurementService
from app.services.history_service import HistoryService
from .controller import UIController


def create_controller(path: str | Path | None = None) -> UIController:
    database = Database(path)
    measurements = MeasurementRepository(database)
    return UIController(ProfileService(ProfileRepository(database),measurements),
                        MeasurementService(measurements), HistoryService(measurements))

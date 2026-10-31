"""Controlled errors; SQL details remain in chained exceptions only."""
class DatabaseError(Exception):
    """Storage is unavailable or an operation failed."""
class InitializationError(DatabaseError):
    """Storage could not be initialized."""
class IntegrityError(DatabaseError):
    """Stored data would violate a constraint."""
class ProfileNotFound(DatabaseError):
    """The requested local profile does not exist."""
class MeasurementNotFound(DatabaseError):
    """The selected profile has no such measurement."""

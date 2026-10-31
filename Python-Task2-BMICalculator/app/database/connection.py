"""Short-lived connections, explicit transactions and configurable local storage."""
from contextlib import contextmanager
from collections.abc import Iterator, Callable
import os
from pathlib import Path
import sqlite3
import sys
from .errors import DatabaseError, InitializationError, IntegrityError
from .schema import STATEMENTS, SCHEMA_VERSION

def default_database_path() -> Path:
    """Use an override, or user-specific platform application data."""
    override = os.environ.get("BMI_INSIGHT_DATA_DIR")
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "NOMOLI_FORGE" / "BMI_Insight"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "NOMOLI_FORGE" / "BMI_Insight"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "nomoli-forge" / "bmi-insight"
    return base / "bmi_insight.sqlite3"

class Database:
    """Inject a temporary file path in tests. Each context owns its connection."""
    def __init__(self, path: str | Path | None = None,
                 connection_factory: Callable[..., sqlite3.Connection] = sqlite3.connect):
        self.path = Path(path) if path is not None else default_database_path()
        self.factory = connection_factory
        if str(path) == ":memory:":
            raise InitializationError("Use a temporary file database with short-lived connections.")
        self.initialize()

    @contextmanager
    def connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        connection = None
        try:
            connection = self.factory(str(self.path), timeout=5)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise DatabaseError("Database relationship protection is unavailable.")
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            if write:
                connection.commit()
        except sqlite3.IntegrityError as exc:
            if connection is not None:
                connection.rollback()
            raise IntegrityError("The operation violates a database constraint.") from exc
        except (sqlite3.Error, OSError) as exc:
            if connection is not None:
                connection.rollback()
            raise DatabaseError("Database operation failed. Check storage access and try again.") from exc
        except BaseException:
            if connection is not None and write:
                connection.rollback()
            raise
        finally:
            if connection is not None:
                connection.close()

    def initialize(self) -> None:
        """Create missing parent directories and initialize schema atomically."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.connection(write=True) as connection:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if version not in (0, SCHEMA_VERSION):
                    raise InitializationError("This database version is not supported.")
                for statement in STATEMENTS:
                    connection.execute(statement)
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        except (DatabaseError, OSError) as exc:
            raise InitializationError("Could not initialize BMI Insight storage. Check the data directory.") from exc
